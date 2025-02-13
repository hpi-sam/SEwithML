import io
import logging
from typing import Any, Callable, Optional, TypedDict

import pandas as pd
from langchain.chat_models.base import BaseChatModel
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langgraph.graph import END, START, StateGraph

from prompts import (fix_similarities_prompt, fix_test_smell_prompt,
                     has_test_smell_router_prompt, write_test_case_prompt)
from utils.code_processing import RouteTest, sanitize_code_output
from utils.logging import log_node_execution


class GraphState(TypedDict):
    """Type definition for the graph state"""

    code_to_test: str
    coverage_matrix: str
    unit_test: str
    vector_store: InMemoryVectorStore
    improvements_remaining: int
    identified_smells: str
    uncovered_lines: list[dict[str, Any]]


class LangChainGraph:
    """Central API for LangChain graph operations"""

    @staticmethod
    def create_unit_test_graph(
        llm: BaseChatModel,
        detailed_logger: logging.Logger,
        minimal_logger: logging.Logger,
        log_callback: Optional[Callable] = None,
        similarity_comparison_count: int = 1,
    ) -> StateGraph:
        """Creates and returns a compiled state graph for unit test generation"""

        def update_logs():
            """Helper function to update logs if callback is provided"""
            if log_callback:
                log_callback()

        def write_initial_test(state: GraphState) -> dict[str, Any]:
            """Node function to write the initial unit test"""
            # Get edge case tests first
            existing_edge_case_tests_result = state["vector_store"].similarity_search(
                "Unit test that tests an edge case", k=similarity_comparison_count
            )
            existing_edge_case_tests = "\n\n".join(
                [
                    f"Existing Test Case {i+1}:\n```python\n{result.page_content}\n```"
                    for i, result in enumerate(existing_edge_case_tests_result)
                ]
            )

            log_node_execution(
                (detailed_logger, minimal_logger),
                "write_initial_test",
                inputs={
                    "code_to_test": state["code_to_test"],
                    "coverage_matrix": state["coverage_matrix"],
                    "uncovered_lines": state["uncovered_lines"],
                    "existing_edge_case_tests": existing_edge_case_tests,
                },
            )
            update_logs()

            uncovered_lines_txt = (
                "\n".join(f"Line {line['line_number']}: {line['line']}" for line in state["uncovered_lines"])
                if len(state["uncovered_lines"])
                else "None"
            )

            response = llm.invoke(
                write_test_case_prompt.format(
                    code_to_test=state["code_to_test"],
                    coverage_matrix=state["coverage_matrix"],
                    uncovered_lines=uncovered_lines_txt,
                    existing_tests=existing_edge_case_tests,
                )
            )
            output = {"unit_test": sanitize_code_output(str(response.content))}
            log_node_execution((detailed_logger, minimal_logger), "write_initial_test", outputs=output)
            return output

        def fix_similarities(state: GraphState) -> dict[str, Any]:
            """Node function to fix similarities with existing tests"""
            similar_tests = state["vector_store"].similarity_search(state["unit_test"], k=similarity_comparison_count)
            existing_tests = "\n\n".join(
                [
                    f"Existing Unit Test {i+1}:\n```python\n{result.page_content}\n```"
                    for i, result in enumerate(similar_tests)
                ]
            )

            uncovered_lines_txt = (
                "\n".join(f"Line {line['line_number']}: {line['line']}" for line in state["uncovered_lines"])
                if len(state["uncovered_lines"])
                else "None"
            )

            log_node_execution(
                (detailed_logger, minimal_logger),
                "fix_similarities",
                inputs={
                    "unit_test": state["unit_test"],
                    "existing_tests": existing_tests,
                    "coverage_matrix": state["coverage_matrix"],
                    "uncovered_lines": uncovered_lines_txt,
                },
            )

            update_logs()
            response = llm.invoke(
                fix_similarities_prompt.format(
                    code_to_test=state["code_to_test"],
                    existing_unit_tests=existing_tests,
                    new_unit_test=state["unit_test"],
                    coverage_matrix=state["coverage_matrix"],
                    uncovered_lines=uncovered_lines_txt,
                )
            )
            output = {"unit_test": sanitize_code_output(str(response.content))}
            log_node_execution((detailed_logger, minimal_logger), "fix_similarities", outputs=output)
            return output

        def has_test_smell_router(state: GraphState) -> dict[str, Any]:
            """Node function to route based on test smells"""
            if state["improvements_remaining"] <= 0:
                output = {
                    "destination": "keep_good_test",
                    "unit_test": state["unit_test"],
                }
                log_node_execution(
                    (detailed_logger, minimal_logger),
                    "has_test_smell_router",
                    outputs=output,
                )
                return output

            log_node_execution(
                (detailed_logger, minimal_logger),
                "has_test_smell_router",
                inputs={"unit_test": state["unit_test"]},
            )

            update_logs()
            response = llm.with_structured_output(RouteTest).invoke(
                has_test_smell_router_prompt.format(code_to_test=state["code_to_test"], unit_test=state["unit_test"])
            )
            output = {
                "destination": response.destination,
                "identified_smells": response.identified_smells,
            }
            log_node_execution(
                (detailed_logger, minimal_logger),
                "has_test_smell_router",
                outputs=output,
            )
            return output

        def fix_test_smell(state: GraphState) -> dict[str, Any]:
            """Node function to fix identified test smells"""
            log_node_execution(
                (detailed_logger, minimal_logger),
                "fix_test_smell",
                inputs={
                    "unit_test": state["unit_test"],
                    "identified_smells": state["identified_smells"],
                },
            )

            update_logs()
            response = llm.invoke(
                fix_test_smell_prompt.format(
                    code_to_test=state["code_to_test"],
                    unit_test=state["unit_test"],
                    identified_smells=state["identified_smells"],
                )
            )
            output = {
                "unit_test": sanitize_code_output(str(response.content)),
                "improvements_remaining": state["improvements_remaining"] - 1,
                "identified_smells": "",
            }
            log_node_execution((detailed_logger, minimal_logger), "fix_test_smell", outputs=output)
            return output

        def add_to_vectorstore(state: GraphState) -> dict[str, Any]:
            """Node function to add the final test to the vector store"""
            log_node_execution(
                (detailed_logger, minimal_logger),
                "add_to_vectorstore",
                inputs={"unit_test": state["unit_test"]},
            )

            new_test_doc = Document(page_content=state["unit_test"], metadata={"type": "unit_test"})
            state["vector_store"].add_documents([new_test_doc])
            output = {"vector_store": state["vector_store"]}
            log_node_execution((detailed_logger, minimal_logger), "add_to_vectorstore", outputs=output)
            return output

        # Build graph
        builder = StateGraph(GraphState)

        # Add nodes
        builder.add_node("write_initial_test", write_initial_test)
        builder.add_node("fix_similarities", fix_similarities)
        builder.add_node("has_test_smell_router", has_test_smell_router)
        builder.add_node("fix_test_smell", fix_test_smell)
        builder.add_node("add_to_vectorstore", add_to_vectorstore)

        # Add edges
        builder.add_edge(START, "write_initial_test")
        builder.add_edge("write_initial_test", "fix_similarities")
        builder.add_edge("fix_similarities", "has_test_smell_router")
        builder.add_conditional_edges(
            "has_test_smell_router",
            lambda state: state["destination"],
            {
                "fix_test_smell": "fix_test_smell",
                "keep_good_test": "add_to_vectorstore",
            },
        )
        builder.add_edge("fix_test_smell", "has_test_smell_router")
        builder.add_edge("add_to_vectorstore", END)

        return builder.compile()
