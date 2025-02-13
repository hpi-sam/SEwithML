import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, TextIO


def get_next_run_dir() -> Path:
    """
    Get the next available run directory (e.g., run1, run2, etc.)

    Returns:
        Path to the next run directory
    """
    runs_dir = Path("runs")
    runs_dir.mkdir(parents=True, exist_ok=True)

    existing_runs = [d for d in runs_dir.iterdir() if d.is_dir() and d.name.startswith("run")]
    if not existing_runs:
        next_run = runs_dir / "run1"
    else:
        run_numbers = [int(run.name[3:]) for run in existing_runs]
        next_run = runs_dir / f"run{max(run_numbers) + 1}"

    # Create the run directory
    next_run.mkdir(parents=True, exist_ok=True)
    return next_run


def save_code_files(
    run_dir: Path,
    code_to_test: str,
    existing_tests: list[str],
    generated_test_case: str,
    combined_test_script: str,
):
    """
    Save code and test files in the run directory

    Args:
        run_dir: Path to the run directory
        code_to_test: Source code being tested
        existing_tests: List of existing test cases
        generated_test_case: Generated test case
        combined_test_script: Combined test script
    """
    # Save source code
    with open(run_dir / "code_to_test.py", "w") as f:
        f.write(code_to_test)

    # Save existing tests
    for i, test in enumerate(existing_tests, 1):
        if test.strip():  # Only save non-empty tests
            with open(run_dir / f"existing_test_{i}.py", "w") as f:
                f.write(test)

    # Save generated test
    with open(run_dir / "generated_test_case.py", "w") as f:
        f.write(generated_test_case)

    # Save combined test script
    with open(run_dir / "combined_test_script.py", "w") as f:
        f.write(combined_test_script)


def setup_logging(config: dict[str, Any], stream: Optional[TextIO] = None) -> tuple[logging.Logger, logging.Logger]:
    """
    Set up logging configuration with separate loggers for detailed and minimal logging

    Returns:
        Tuple of (detailed_logger, minimal_logger)
    """
    if not config.get("enabled", True):
        return logging.getLogger("detailed"), logging.getLogger("minimal")

    # Create or get run directory
    if hasattr(setup_logging, "current_run_dir"):
        run_dir = setup_logging.current_run_dir
    else:
        run_dir = get_next_run_dir()
        setup_logging.current_run_dir = run_dir

    # Create loggers
    detailed_logger = logging.getLogger("unit_test_generator.detailed")
    minimal_logger = logging.getLogger("unit_test_generator.minimal")

    for logger in [detailed_logger, minimal_logger]:
        logger.setLevel(getattr(logging, config.get("level", "INFO")))
        logger.handlers.clear()

    # Create formatters
    formatter = logging.Formatter(
        fmt=config.get("format", "%(asctime)s - %(levelname)s - %(message)s"),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handlers with timestamp
    if config.get("file_logging", True):
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

        # Detailed log file
        detailed_file = run_dir / f"{timestamp}_detailed.log"
        detailed_handler = logging.FileHandler(detailed_file, encoding="utf-8")
        detailed_handler.setFormatter(formatter)
        detailed_logger.addHandler(detailed_handler)

        # Minimal log file
        minimal_file = run_dir / f"{timestamp}_minimal.log"
        minimal_handler = logging.FileHandler(minimal_file, encoding="utf-8")
        minimal_handler.setFormatter(formatter)
        minimal_logger.addHandler(minimal_handler)

    # Stream handler (only for minimal logs)
    if config.get("console_logging", True) and stream:
        stream_handler = logging.StreamHandler(stream)
        stream_handler.setFormatter(formatter)
        minimal_logger.addHandler(stream_handler)

    return detailed_logger, minimal_logger


def log_node_execution(
    loggers: tuple[logging.Logger, logging.Logger],
    node_name: str,
    inputs: Optional[Dict[str, Any]] = None,
    outputs: Optional[Dict[str, Any]] = None,
):
    """
    Log node execution with both detailed and minimal formats

    Args:
        loggers: Tuple of (detailed_logger, minimal_logger)
        node_name: Name of the node being executed
        inputs: Optional dictionary of input parameters
        outputs: Optional dictionary of output parameters
    """
    detailed_logger, minimal_logger = loggers

    def format_value_minimal(v):
        if isinstance(v, str):
            return f"(str, length: {len(v)})"
        elif isinstance(v, list):
            return f"(list, length: {len(v)})"
        elif isinstance(v, dict):
            return f"(dict, length: {len(v)})"
        else:
            return f"({type(v).__name__})"

    # Detailed logging
    msg_parts_detailed = [f"Node: {node_name}"]
    if inputs:
        input_params = ", ".join(f"{k}={v}" for k, v in inputs.items())
        msg_parts_detailed.append(f"Inputs: {input_params}")
    if outputs:
        output_params = ", ".join(f"{k}={v}" for k, v in outputs.items())
        msg_parts_detailed.append(f"Outputs: {output_params}")
    detailed_logger.info(" | ".join(msg_parts_detailed))

    # Minimal logging
    msg_parts_minimal = [f"Node: {node_name}"]
    if inputs:
        input_params = ", ".join(f"{k} {format_value_minimal(v)}" for k, v in inputs.items())
        msg_parts_minimal.append(f"Inputs: {input_params}")
    if outputs:
        output_params = ", ".join(f"{k} {format_value_minimal(v)}" for k, v in outputs.items())
        msg_parts_minimal.append(f"Outputs: {output_params}")
    minimal_logger.info(" | ".join(msg_parts_minimal))
