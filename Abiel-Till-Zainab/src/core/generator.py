import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Callable, List, Optional

from langchain_community.embeddings import JinaEmbeddings
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from core.langchain_graph import LangChainGraph
from utils.code_processing import (assemble_test_script, extract_unit_tests,
                                   sanitize_code_output)
from utils.logging import log_node_execution
from utils.metrics import analyze_test_coverage


class UnitTestGenerator:
    def __init__(self, cfg: dict[str, Any], loggers: tuple[logging.Logger, logging.Logger]):
        """Initialize the generator with settings and loggers"""
        self.cfg = cfg
        self.detailed_logger, self.minimal_logger = loggers
        self.llm = None
        self.embedding_model = None
        self.vector_store = None
        self.existing_test_cases: List[str] = []
        self._initialize_models()

    def _initialize_models(self):
        """Initialize LLM and embedding models based on settings"""
        openai_models = ["o1", "o1-mini"] # let them stay here eventhough they won't be used in our openai api tiers
        model_name = self.cfg["llm"]["model_name"].lower()
        if "gpt" in model_name or model_name in openai_models:
            self.llm = ChatOpenAI(
                model=self.cfg["llm"]["model_name"],
                temperature=0.3,
                top_p=0.95,
                api_key=self.cfg["api"]["openai_api_key"],
            )
            self.embedding_model = OpenAIEmbeddings(api_key=self.cfg["api"]["openai_api_key"])
        else:
            self.llm = ChatGroq(
                name="llama-3.3-70b-specdec",
                temperature=0.0,
                api_key=self.cfg["api"]["groq_api_key"],
                stop_sequences=None,
            )
            self.embedding_model = JinaEmbeddings(
                jina_api_key=self.cfg["api"]["jina_api_key"],
                model_name="jina-embeddings-v3",
            )
        self.detailed_logger.info(f"Initialized models - LLM: {self.cfg['llm']['model_name']}")
        self.minimal_logger.info(f"Models initialized")

    def initialize_vector_store(self, existing_tests: str = "") -> List[str]:
        """Initialize vector store with existing tests"""
        self.existing_test_cases = extract_unit_tests(existing_tests) if existing_tests else []
        test_documents = [
            Document(page_content=test_case, metadata={"type": "unit_test"}) for test_case in self.existing_test_cases
        ]
        self.vector_store = InMemoryVectorStore.from_documents(test_documents, self.embedding_model)
        self.detailed_logger.info(f"Initialized vector store with {len(self.existing_test_cases)} existing tests")
        return self.existing_test_cases

    def generate_test(
        self,
        code_to_test: str,
        coverage_matrix: str,
        uncovered_lines: list,
        log_callback: Optional[Callable] = None,
    ) -> dict[str, str]:
        """Generate a unit test for the given code"""
        if self.vector_store is None:
            self.initialize_vector_store()

        self.detailed_logger.info("Creating unit test graph")
        self.minimal_logger.info("Graph creation started")

        # Create graph and invoke it
        graph = LangChainGraph.create_unit_test_graph(
            self.llm,
            self.detailed_logger,
            self.minimal_logger,
            log_callback,
            self.cfg["llm"]["similarity_comparison_count"],
        )

        initial_state = {
            "code_to_test": code_to_test,
            "coverage_matrix": coverage_matrix,
            "uncovered_lines": uncovered_lines,
            "vector_store": self.vector_store,
            "improvements_remaining": self.cfg["llm"]["max_improvements"],
            "identified_smells": "",
            "unit_test": "",
        }

        # Update logs before starting
        if log_callback:
            log_callback()

        result = graph.invoke(initial_state)

        return {
            "generated_test_case": result["unit_test"],
            "combined_test_script": assemble_test_script("code_to_test", self.existing_test_cases, result["unit_test"]),
        }
