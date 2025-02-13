import io
import json
import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import streamlit as st

from config import APIConfig
from core.generator import UnitTestGenerator
from utils.code_processing import (assemble_test_script, extract_unit_tests,
                                   sanitize_code_output,
                                   validate_python_syntax)
from utils.logging import (get_next_run_dir, log_node_execution,
                           save_code_files, setup_logging)
from utils.metrics import analyze_test_coverage


def load_config() -> Dict[Any, Any]:
    """Load configuration from config.json or return default"""
    try:
        with open("src/config/config.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "model_choice": "gpt-4o-mini",
            "max_improvements": 2,
            "similarity_comparison_count": 10,
        }


def save_config(config: Dict[Any, Any]):
    """Save configuration to config.json"""
    with open("src/config/config.json", "w") as f:
        json.dump(config, f, indent=2)


def save_run(
    cfg: dict[str, Any],
    code_to_test: str,
    existing_tests: list[str],
    generated_test_case: str,
    combined_test_script: str,
    logs: str,
):
    """Save the current run to history"""
    # Use the same run directory that was created for logging
    run_dir = setup_logging.current_run_dir

    # Save code and test files
    save_code_files(
        run_dir, code_to_test, existing_tests, generated_test_case, combined_test_script
    )

    # Add validation of generated test
    validation_error = validate_python_syntax(generated_test_case)
    run_data = {
        "timestamp": datetime.now().isoformat(),
        "code_to_test": code_to_test,
        "existing_tests": existing_tests,
        "generated_test_case": generated_test_case,
        "combined_test_script": combined_test_script,
        "validation_error": validation_error,
        "logs": logs,
        "model": cfg["llm"]["model_name"],
        "max_improvements": cfg["llm"]["max_improvements"],
        "similarity_comparison_count": cfg["llm"]["similarity_comparison_count"],
    }

    # Save to file in the run directory
    filename = run_dir / "run_data.json"
    with open(filename, "w") as f:
        json.dump(run_data, f, indent=2)

    # Add to session state
    if "run_history" not in st.session_state:
        st.session_state.run_history = []
    st.session_state.run_history.append(run_data)


def init_session_state():
    """Initialize Streamlit session state"""
    config = load_config()

    # Load API keys from environment
    api_config = APIConfig.from_env()

    if "existing_tests" not in st.session_state:
        st.session_state.existing_tests = [""]
    if "model_choice" not in st.session_state:
        st.session_state.model_choice = config["model_choice"]
    if "max_improvements" not in st.session_state:
        st.session_state.max_improvements = config["max_improvements"]
    if "max_tests" not in st.session_state:
        st.session_state.max_tests = config.get("max_tests", 10)
    if "settings" not in st.session_state:
        st.session_state.settings = {
            "llm": {
                "model_name": config["model_choice"],
                "max_improvements": config["max_improvements"],
                "similarity_comparison_count": config.get(
                    "similarity_comparison_count", 1
                ),
            },
            "api": {
                "openai_api_key": api_config.openai_api_key.get_secret_value(),
                "groq_api_key": api_config.groq_api_key.get_secret_value(),
                "jina_api_key": api_config.jina_api_key.get_secret_value(),
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "enabled": True,
                "file_logging": True,
                "console_logging": True,
            },
        }
    if "generator" not in st.session_state:
        st.session_state.generator = None
    if "run_history" not in st.session_state:
        st.session_state.run_history = []
    if "last_generated_test" not in st.session_state:
        st.session_state.last_generated_test = None
    if "last_validation_error" not in st.session_state:
        st.session_state.last_validation_error = None
    if "pending_test" not in st.session_state:
        st.session_state.pending_test = None
    if "auto_generating" not in st.session_state:
        st.session_state.auto_generating = False


def add_test_input():
    """Add a new test input field"""
    # Filter out empty test cases before adding a new one
    st.session_state.existing_tests = [
        test for test in st.session_state.existing_tests if test.strip()
    ]
    st.session_state.existing_tests.append("")


def remove_test_input(index: int):
    """Remove a test input field"""
    st.session_state.existing_tests.pop(index)
    # Filter out empty test cases after removing one
    st.session_state.existing_tests = [
        test for test in st.session_state.existing_tests if test.strip()
    ]
    # Always ensure at least one test input field
    if not st.session_state.existing_tests:
        st.session_state.existing_tests = [""]


def get_available_runs():
    """Get a list of all available runs with their data"""
    runs_dir = Path("runs")
    runs = []
    if runs_dir.exists():
        # Extract run number and create tuples of (number, path)
        run_dirs = []
        for run_dir in runs_dir.glob("run*"):
            try:
                run_number = int(run_dir.name.replace("run", ""))
                run_dirs.append((run_number, run_dir))
            except ValueError:
                continue

        # Sort by run number in descending order
        for _, run_dir in sorted(run_dirs, reverse=True):
            run_data_file = run_dir / "run_data.json"
            if run_data_file.exists():
                try:
                    with open(run_data_file, "r") as f:
                        data = json.load(f)
                        # Clean up the code preview
                        code_lines = data["code_to_test"].splitlines()
                        for line in code_lines:
                            if "def " in line:
                                # Extract function signature without 'def' and ':'
                                code_preview = line.strip()
                                code_preview = code_preview.replace("def ", "").replace(
                                    ":", ""
                                )
                                break
                        else:
                            code_preview = "unknown"

                        runs.append(
                            {
                                "id": run_dir.name,
                                "code_preview": code_preview,
                                "data": data,
                            }
                        )
                except Exception:
                    continue
    return runs


def load_run_data(run_data: dict):
    """Load code and tests from a previous run and reset output state"""
    # Load code and tests
    st.session_state.existing_tests = run_data["existing_tests"].copy()

    # Add the generated test case to existing tests if it exists
    if "generated_test_case" in run_data and run_data["generated_test_case"]:
        st.session_state.existing_tests.append(run_data["generated_test_case"])

    # Create a mock test case to enable the test execution functionality
    st.session_state.last_generated_test = run_data.get("combined_test_script")
    st.session_state.last_validation_error = None
    st.session_state.pending_test = None

    return run_data["code_to_test"]


def execute_test_script(
    test_script: str,
) -> tuple[bool, str, pd.DataFrame, Dict[str, Any]]:
    """Execute a test script and return the results, coverage matrix, and raw metrics"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        # Get current code and tests
        current_code = st.session_state["code_to_test_input"]
        existing_tests = [
            test for test in st.session_state.existing_tests if test.strip()
        ]

        # Process existing tests and ensure proper indentation
        processed_tests = []
        for test in existing_tests:
            extracted_tests = extract_unit_tests(test)
            for extracted_test in extracted_tests:
                # Ensure consistent indentation for the test body
                lines = extracted_test.split("\n")
                if len(lines) > 1:
                    # Keep first line (def statement) as is
                    indented_lines = [lines[0]]
                    # Indent all other lines with 4 spaces if they're not empty
                    for line in lines[1:]:
                        if line.strip():
                            # Calculate original indentation
                            original_indent = len(line) - len(line.lstrip())
                            # Add 4 spaces plus original indentation
                            indented_lines.append(
                                "    " + " " * original_indent + line.lstrip()
                            )
                        else:
                            indented_lines.append("")
                    processed_tests.append("\n".join(indented_lines))
                else:
                    processed_tests.append(extracted_test)

        # Create the combined test script
        combined_test_script = assemble_test_script(
            "code_to_test.py", processed_tests, ""
        )

        # Write files
        code_file = temp_dir_path / "code_to_test.py"
        test_file = temp_dir_path / "combined_test_script.py"

        with open(code_file, "w") as f:
            f.write(current_code)

        with open(test_file, "w") as f:
            f.write(combined_test_script)

        try:
            # Add temp directory to PYTHONPATH
            env = os.environ.copy()
            env["PYTHONPATH"] = str(temp_dir_path)

            # Change to temp directory
            current_dir = os.getcwd()
            os.chdir(temp_dir_path)

            # Run tests and get results
            result = subprocess.run(
                ["python", "-m", "unittest", "combined_test_script.py"],
                capture_output=True,
                text=True,
                env=env,
            )

            # Get test case names from the combined script
            test_cases = []
            for test in processed_tests:
                if test.startswith("def test_"):
                    test_name = test.split("(")[0].replace("def ", "")
                    test_cases.append(test_name)

            # Generate coverage matrix
            success = result.returncode == 0
            matrix_df, raw_results = analyze_test_coverage(
                str(code_file), "combined_test_script", test_cases
            )

            # Extract uncovered lines
            uncovered_lines = []
            for idx, row in matrix_df.iterrows():
                if idx != "Col Sum" and row["Coverage"] == 0:
                    uncovered_lines.append(
                        {"line_number": idx, "line": row["Code"].strip()}
                    )
            raw_results["uncovered_lines"] = uncovered_lines

            # Change back to original directory
            os.chdir(current_dir)

            return success, result.stdout + result.stderr, matrix_df, raw_results

        except Exception as e:
            return False, str(e), pd.DataFrame(), {}


def format_test_code(test_code: str) -> str:
    """Format test code using black."""
    if not test_code.strip():
        return ""

    try:
        import black

        return black.format_str(test_code, mode=black.FileMode())
    except Exception:
        # Return original code if formatting fails
        return test_code


def clear_input_fields():
    """Clear all input fields and start a new run"""
    st.session_state.existing_tests = [""]  # Reset to single empty test
    st.session_state.code_to_test_input = ""  # Clear code input
    st.session_state.last_generated_test = None
    st.session_state.last_validation_error = None
    st.session_state.pending_test = None
    st.session_state.auto_generating = False
    if "loaded_code" in st.session_state:
        del st.session_state.loaded_code
    if "loaded_combined_test" in st.session_state:
        del st.session_state.loaded_combined_test
    
    # Reset the current run directory to force creation of a new one
    if hasattr(setup_logging, 'current_run_dir'):
        delattr(setup_logging, 'current_run_dir')


def main():
    """Main Streamlit application"""
    # Load environment variables at startup
    from dotenv import load_dotenv

    load_dotenv()

    st.set_page_config(page_title="Unit Test Generator", page_icon="🧪", layout="wide")

    init_session_state()

    st.title("🧪 Agentic Unit Test Generator")
    st.subheader(
        """:blue[Improve coverage with readable, targeted, complementary test cases.]""",
        divider=True,
    )

    # Settings sidebar
    with st.sidebar:
        st.header("Settings")

        # Add run selector at the top of the sidebar
        st.subheader("📂 Load Previous Runs")
        runs = get_available_runs()
        if runs:
            # Create options list with "Previous Run" at the top
            options = [
                {
                    "id": "previous_run",
                    "code_preview": runs[0]["code_preview"],
                    "data": runs[0]["data"],
                }
            ] + runs
            selected_run = st.selectbox(
                "Select a run",
                options=options,
                format_func=lambda x: "Most Recent Run"
                if x["id"] == "previous_run"
                else f"{x['id']} - {x['code_preview']}",
            )
            if selected_run and st.button("Load Selected Run", icon="📥"):
                code_to_test = load_run_data(selected_run["data"])
                st.session_state.loaded_code = code_to_test
                st.rerun()

        st.divider()

        st.subheader("Model")
        model_choice = st.selectbox(
            "Select Model",
            ["gpt-4o", "gpt-4o-mini", "o1-mini", "o1"],
            index=["gpt-4o", "gpt-4o-mini", "o1-mini", "o1"].index(st.session_state.model_choice),
        )
        max_improvements = st.slider(
            "Maximum Test Improvements",
            min_value=1,
            max_value=5,
            value=st.session_state.max_improvements,
            help="Maximum number of improvement iterations for each generated test",
        )
        similarity_count = st.slider(
            "Similar Tests to Compare",
            min_value=1,
            max_value=20,
            value=st.session_state.settings["llm"]["similarity_comparison_count"],
            help="Number of existing tests to compare for similarity",
        )
        max_tests = st.slider(
            "Maximum Tests to Generate",
            min_value=1,
            max_value=50,
            value=25,
            help="Maximum number of tests to generate when aiming for 100% coverage",
        )

        # Save config when changed
        if (
            model_choice != st.session_state.model_choice
            or max_improvements != st.session_state.max_improvements
            or similarity_count
            != st.session_state.settings["llm"]["similarity_comparison_count"]
            or (
                "max_tests" not in st.session_state
                or max_tests != st.session_state.max_tests
            )
        ):
            config = {
                "model_choice": model_choice,
                "max_improvements": max_improvements,
                "similarity_comparison_count": similarity_count,
                "max_tests": max_tests,
            }
            save_config(config)
            st.session_state.model_choice = model_choice
            st.session_state.max_improvements = max_improvements
            st.session_state.settings["llm"][
                "similarity_comparison_count"
            ] = similarity_count
            st.session_state.max_tests = max_tests

    # Main content
    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("Input")
        
        # Add Clear All button in a small column
        clear_col1, clear_col2 = st.columns([5, 1])
        with clear_col2:
            if st.button("🗑️ Clear All"):
                clear_input_fields()
                st.rerun()
        
        code_input_key = "code_to_test_input"
        if "loaded_code" in st.session_state:
            st.session_state[code_input_key] = st.session_state.loaded_code
            del st.session_state.loaded_code

        code_to_test = st.text_area(
            "Code to Test",
            key=code_input_key,
            height=300,
            placeholder="Paste your Python code here...",
        )

        st.subheader("Existing Unit Tests")
        for i, test in enumerate(st.session_state.existing_tests):
            col_test, col_remove = st.columns([6, 1])
            with col_test:
                new_test = st.text_area(
                    f"Test #{i+1}",
                    value=test,
                    height=150,
                    key=f"test_{i}",
                    placeholder="Paste an existing unit test here (optional)...",
                )
                # Format the test code if it changed
                if new_test != test:
                    formatted_test = format_test_code(new_test)
                    st.session_state.existing_tests[i] = formatted_test
                    if formatted_test != new_test:
                        st.rerun()  # Refresh to show formatted code

            with col_remove:
                if len(st.session_state.existing_tests) > 1:
                    if st.button("🗑️", key=f"remove_{i}"):
                        remove_test_input(i)
                        st.rerun()

        if st.button("Add Another Test", icon="➕"):
            add_test_input()
            st.rerun()

    with col2:
        st.header("Output")

        # Create a row of buttons
        button_cols = st.columns([3, 3, 1, 1])
        with button_cols[0]:
            generate_clicked = st.button("🚀 Generate Test Case", type="primary")
        with button_cols[1]:
            generate_until_coverage = st.button(
                "🎯 Generate until Full Coverage", type="primary"
            )

        # Only show accept/reject if there's a pending test and we're not in auto-generate mode
        if st.session_state.pending_test and not generate_until_coverage:
            with button_cols[2]:
                if st.button("Accept", type="secondary", icon="✅"):
                    # Only append if it's an actual test case
                    if (
                        st.session_state.pending_test != "Applied"
                        and st.session_state.pending_test != "Rejected"
                    ):
                        # Remove any empty tests and initialize with empty list
                        st.session_state.existing_tests = [
                            test
                            for test in st.session_state.existing_tests
                            if test.strip()
                        ]
                        st.session_state.existing_tests.append(
                            st.session_state.pending_test
                        )
                        st.session_state.pending_test = "Applied"
                        st.rerun()
            with button_cols[3]:
                if st.button("Reject", type="secondary", icon="❌"):
                    if (
                        st.session_state.pending_test != "Applied"
                        and st.session_state.pending_test != "Rejected"
                    ):
                        st.session_state.pending_test = "Rejected"
                        st.rerun()

        # Show combined test script from loaded run if available
        if (
            "loaded_combined_test" in st.session_state
            and st.session_state.loaded_combined_test
        ):
            with st.expander("Combined Test Script", expanded=True):
                st.code(st.session_state.loaded_combined_test, language="python")

            # Add the "Run Existing Unit Tests" button when a run is loaded
            run_tests_loaded = st.button(
                "Run Existing Unit Tests", type="secondary", icon="▶️"
            )
            if run_tests_loaded:
                with st.spinner("Running tests..."):
                    success, output, matrix_df, raw_results = execute_test_script(
                        st.session_state.loaded_combined_test
                    )
                if success:
                    st.success("✅ All tests passed!")
                else:
                    st.error("❌ Some tests failed")

        if generate_clicked or generate_until_coverage:
            if not code_to_test.strip():
                st.error("Please enter some code to test!")
                return

            try:
                # Create a placeholder for logs before generation starts
                log_placeholder = st.empty()
                log_stream = io.StringIO()
                settings = st.session_state.settings
                detailed_logger, minimal_logger = setup_logging(
                    settings["logging"], stream=log_stream
                )

                # Process existing tests
                existing_tests = [
                    test for test in st.session_state.existing_tests if test.strip()
                ]
                processed_tests = []
                for test in existing_tests:
                    processed_tests.extend(extract_unit_tests(test))

                existing_tests_str = "\n".join(processed_tests)

                # Initialize generator
                if not st.session_state.generator:
                    st.session_state.generator = UnitTestGenerator(
                        settings, (detailed_logger, minimal_logger)
                    )

                st.session_state.generator.initialize_vector_store(existing_tests_str)

                # Get coverage matrix and uncovered lines before generating test
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_dir_path = Path(temp_dir)

                    # Create the combined test script
                    combined_test_script = assemble_test_script(
                        "code_to_test.py", processed_tests, ""
                    )

                    # Write files
                    code_file = temp_dir_path / "code_to_test.py"
                    test_file = temp_dir_path / "combined_test_script.py"

                    with open(code_file, "w") as f:
                        f.write(code_to_test)

                    with open(test_file, "w") as f:
                        f.write(combined_test_script)

                    # Get test case names
                    test_cases = []
                    for test in processed_tests:
                        if test.startswith("def test_"):
                            test_name = test.split("(")[0].replace("def ", "")
                            test_cases.append(test_name)

                    # Generate coverage matrix
                    matrix_df, raw_results = analyze_test_coverage(
                        str(code_file), "combined_test_script", test_cases
                    )

                    # Extract uncovered lines
                    uncovered_lines = []
                    for idx, row in matrix_df.iterrows():
                        if idx != "Col Sum" and row["Coverage"] == 0:
                            uncovered_lines.append(
                                {"line_number": idx, "line": row["Code"].strip()}
                            )

                # Move result storage outside the spinner
                result = None
                with st.spinner("Generating unit test..."):

                    def update_logs():
                        with log_placeholder.container():
                            with st.expander("🔄 Generation Progress", expanded=True):
                                st.text(log_stream.getvalue())

                    result = st.session_state.generator.generate_test(
                        code_to_test,
                        matrix_df.to_markdown(index=True),
                        uncovered_lines,
                        log_callback=update_logs,
                    )
                    update_logs()

                if result:
                    generated_test_case = result["generated_test_case"]
                    combined_test_script = sanitize_code_output(
                        result["combined_test_script"]
                    )

                    # Save run before adding to existing tests
                    save_run(
                        settings,
                        code_to_test,
                        processed_tests,
                        generated_test_case,
                        combined_test_script,
                        log_stream.getvalue(),
                    )

                    # Store results in session state
                    st.session_state.last_generated_test = combined_test_script
                    st.session_state.last_validation_error = validate_python_syntax(
                        generated_test_case
                    )

                    # Handle auto-generate mode
                    if generate_until_coverage:
                        st.session_state.auto_generating = True
                        current_coverage = 0.0
                        tests_generated = 0

                        # Initialize with empty list and remove any empty tests
                        st.session_state.existing_tests = [
                            test
                            for test in st.session_state.existing_tests
                            if test.strip()
                        ]

                        with st.spinner("Generating tests until 100% coverage..."):
                            while (
                                current_coverage < 1.0
                                and tests_generated < st.session_state.max_tests
                            ):
                                # Auto-accept the test
                                st.session_state.existing_tests.append(
                                    generated_test_case
                                )
                                tests_generated = len(
                                    st.session_state.existing_tests
                                )  # All tests are non-empty now

                                # Get updated coverage after adding the new test
                                with tempfile.TemporaryDirectory() as temp_dir:
                                    temp_dir_path = Path(temp_dir)

                                    # Get all current tests including the newly added one
                                    all_tests = [
                                        test
                                        for test in st.session_state.existing_tests
                                        if test.strip()
                                    ]
                                    processed_tests = []
                                    for test in all_tests:
                                        processed_tests.extend(extract_unit_tests(test))

                                    # Create updated combined test script
                                    updated_combined_script = assemble_test_script(
                                        "code_to_test.py", processed_tests, ""
                                    )

                                    # Write files
                                    code_file = temp_dir_path / "code_to_test.py"
                                    test_file = (
                                        temp_dir_path / "combined_test_script.py"
                                    )

                                    with open(code_file, "w") as f:
                                        f.write(code_to_test)

                                    with open(test_file, "w") as f:
                                        f.write(updated_combined_script)

                                    # Get test case names
                                    test_cases = []
                                    for test in processed_tests:
                                        if test.startswith("def test_"):
                                            test_name = test.split("(")[0].replace(
                                                "def ", ""
                                            )
                                            test_cases.append(test_name)

                                    # Generate updated coverage matrix
                                    matrix_df, raw_results = analyze_test_coverage(
                                        str(code_file),
                                        "combined_test_script",
                                        test_cases,
                                    )
                                    current_coverage = raw_results["line_coverage"]

                                    # Extract updated uncovered lines for next generation
                                    uncovered_lines = []
                                    for idx, row in matrix_df.iterrows():
                                        if idx != "Col Sum" and row["Coverage"] == 0:
                                            uncovered_lines.append(
                                                {"line_number": idx, "line": row["Code"].strip()}
                                            )

                                # Break if we've reached our goals
                                if (
                                    current_coverage >= 1.0
                                    or tests_generated >= st.session_state.max_tests
                                ):
                                    break

                                # Generate next test if needed with updated uncovered lines
                                result = st.session_state.generator.generate_test(
                                    code_to_test,
                                    matrix_df.to_markdown(index=True),
                                    uncovered_lines,  # Pass the updated uncovered lines
                                    log_callback=update_logs,
                                )

                                if result:
                                    generated_test_case = result["generated_test_case"]
                                    combined_test_script = sanitize_code_output(
                                        result["combined_test_script"]
                                    )

                                    # Save run
                                    save_run(
                                        settings,
                                        code_to_test,
                                        processed_tests,
                                        generated_test_case,
                                        combined_test_script,
                                        log_stream.getvalue(),
                                    )
                                else:
                                    break  # Stop if test generation failed

                            # Show final status
                            if current_coverage >= 1.0:
                                st.success("🎯 Success: Achieved 100% coverage!")
                                st.info(
                                    f"Generated {tests_generated} test{'s' if tests_generated != 1 else ''}"
                                )
                            else:
                                st.warning(
                                    "⚠️ Process stopped: Maximum number of tests reached"
                                )
                                st.info(
                                    f"Current coverage: {current_coverage:.1%} with {tests_generated} test{'s' if tests_generated != 1 else ''}"
                                )

                        st.session_state.auto_generating = False
                        st.session_state.pending_test = None
                    else:
                        st.session_state.pending_test = generated_test_case

                    # Force a rerun to update the UI with the new test
                    st.rerun()

            except Exception as e:
                st.session_state.auto_generating = (
                    False  # Reset auto-generating on error
                )
                st.error(f"An error occurred: {str(e)}")

        # Display last generated test if it exists
        if st.session_state.last_generated_test:
            if st.session_state.last_validation_error:
                st.warning(
                    f"⚠️ Generated test case has syntax issues: {st.session_state.last_validation_error}"
                )
            else:
                st.success("✅ Generated test case passed syntax validation")

            # Show the generated test case
            with st.expander("Generated Test Case", expanded=True):
                st.code(st.session_state.pending_test, language="python")

            # Create combined script from only accepted tests
            existing_tests = [
                test for test in st.session_state.existing_tests if test.strip()
            ]
            processed_tests = []
            for test in existing_tests:
                processed_tests.extend(extract_unit_tests(test))

            current_combined_script = assemble_test_script(
                "code_to_test.py", processed_tests, ""  # Don't include pending test
            )

            # Show the combined script
            with st.expander("Combined Test Script", expanded=False):
                st.code(current_combined_script, language="python")

            # Add Run Tests button and results below the test script
            if st.button("Run Existing Unit Tests", type="secondary", icon="▶️"):
                with st.spinner("Running tests..."):
                    success, output, matrix_df, raw_results = execute_test_script(
                        st.session_state.last_generated_test
                    )
                if success:
                    st.success("✅ All tests passed!")
                else:
                    st.error("❌ Some tests failed")

                # Display test results and metrics in tabs
                tab1, tab2, tab3 = st.tabs(
                    ["Test Output", "Coverage Matrix", "Coverage Details"]
                )

                with tab1:
                    st.text(output)

                with tab2:
                    st.dataframe(matrix_df, use_container_width=True)

                with tab3:
                    st.metric("Line Coverage", f"{raw_results['line_coverage']:.1%}")

                    # Display unexecuted lines
                    if raw_results["unexecuted_lines"]:
                        st.subheader("Uncovered Lines")
                        for item in raw_results["unexecuted_lines"]:
                            st.code(f"Line {item['line_number']}: {item['line']}")
                    else:
                        st.success("All lines executed! 🎉")


if __name__ == "__main__":
    main()