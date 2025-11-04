import os
import platform
import sys
import asyncio
import streamlit as st
from datetime import datetime
import json

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

sys.path.extend([os.path.abspath('.'), os.getcwd()])

from playwright_llm_integration.agents import (
    test_suite_generation_agent,
    execute_the_test_case_using_browser_use,
    page_exploration_agent
)
from playwright_llm_integration.utils import STREAMLIT_CSS, AsyncRunner
from playwright_llm_integration.models import TestSuite




# Initialize global async runner
@st.cache_resource
def get_async_runner():
    """Get or create the global async runner."""
    return AsyncRunner()


# ============================================================================
# STREAMLIT APP
# ============================================================================

# Page configuration
st.set_page_config(
    page_title="AI Test Automation Suite",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown(STREAMLIT_CSS, unsafe_allow_html=True)

# Initialize session state
if 'exploration_result' not in st.session_state:
    st.session_state.exploration_result = None
if 'test_suite' not in st.session_state:
    st.session_state.test_suite = None
if 'execution_results' not in st.session_state:
    st.session_state.execution_results = []
if "exploration_final_json" not in st.session_state:
    st.session_state.exploration_final_json = None

# Get async runner
async_runner = get_async_runner()

# Main title
st.markdown('<div class="main-header">🤖 AI-Powered Test Automation Suite</div>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")

    base_url = st.text_input(
        "Base URL",
        value="https://www.saucedemo.com/",
        help="Enter the base URL of the application to test"
    )

    test_description = st.text_area(
        "Test Description",
        height=200,
        placeholder="Enter the test scenario description here...",
        help="Describe what you want to test"
    )

    st.markdown("---")

    # Options
    st.subheader("Execution Options")
    auto_execute = st.checkbox("Auto-execute tests after generation", value=False)
    max_tests = st.number_input("Max tests to execute", min_value=1, max_value=10, value=1)

    st.markdown("---")

    # Actions
    if st.button("🔄 Clear All Results", use_container_width=True):
        st.session_state.exploration_result = None
        st.session_state.test_suite = None
        st.session_state.execution_results = []
        st.rerun()

# Main content area with tabs
tab1, tab2, tab3 = st.tabs([
    "📝 Setup & Test Generation",
    "▶️ Test Execution",
    "📊 Results & Reports"
])

# Tab 1: Page Exploration & Test Suite Generation (Combined)
with tab1:
    st.header("Page Exploration & Test Suite Generation")
    st.markdown("Explore the target application and generate automated test cases.")

    col1, col2 = st.columns([3, 1])

    with col1:
        if test_description:
            st.info(f"**Current Description:** {test_description[:200]}...")

    with col2:
        generate_button = st.button("🔍 Explore & Generate Tests", use_container_width=True, type="primary")

    if generate_button:
        if not base_url or not test_description:
            st.error("Please provide both Base URL and Test Description!")
        else:
            # Step 1: Exploration
            with st.spinner("🔍 Step 1/2: Exploring the page... This may take a moment."):
                try:
                    exploration_result = async_runner.run(
                        page_exploration_agent(base_url, test_description)
                    )
                    st.session_state.exploration_result = exploration_result.final_result()
                    st.session_state.exploration_final_json = exploration_result.structured_output
                    st.success("✅ Page exploration completed successfully!")
                except Exception as e:
                    st.error(f"❌ Error during exploration: {str(e)}")
                    st.exception(e)
                    st.stop()

            # Step 2: Test Suite Generation
            with st.spinner("🧪 Step 2/2: Generating test suite... This may take a minute."):
                try:
                    test_suite = async_runner.run(
                        test_suite_generation_agent(base_url, st.session_state.exploration_result)
                    )
                    st.session_state.test_suite = test_suite
                    st.success("✅ Test suite generated successfully!")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Error during test suite generation: {str(e)}")
                    st.exception(e)
                    st.stop()

            st.rerun()

    # Display exploration results
    if st.session_state.exploration_result:
        st.subheader("Exploration Results")

        with st.expander("View Detailed Exploration Results", expanded=False):
            st.text_area(
                "Exploration Output",
                value=st.session_state.exploration_result,
                height=300,
                disabled=True
            )

        st.download_button(
            label="📥 Download Exploration Results",
            data=st.session_state.exploration_result,
            file_name=f"exploration_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

    # Display test suite
    if st.session_state.test_suite:
        st.markdown("---")
        st.subheader(f"Test Suite: {st.session_state.test_suite.suite_name}")
        st.metric("Total Test Cases", len(st.session_state.test_suite.test_cases))

        # Display each test case
        for idx, test_case in enumerate(st.session_state.test_suite.test_cases, 1):
            with st.expander(f"Test Case #{idx}: {test_case.test_title}"):
                st.markdown(f"**Description:** {test_case.description}")
                st.markdown("**Test Steps:**")
                st.code(test_case.test_steps, language="text")
                st.markdown("**Expected Results:**")
                st.code(test_case.expected_result, language="text")

        # Download test suite
        st.download_button(
            label="📥 Download Test Suite (JSON)",
            data=st.session_state.test_suite.model_dump_json(indent=4),
            file_name=f"test_suite_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

# Tab 2: Test Execution
with tab2:
    st.header("Test Execution")
    st.markdown("Execute generated test cases and monitor results.")

    if not st.session_state.test_suite:
        st.warning("⚠️ Please generate a test suite first!")
    else:
        st.info(f"Ready to execute {len(st.session_state.test_suite.test_cases)} test case(s)")

        # Test selection
        selected_tests = st.multiselect(
            "Select tests to execute",
            options=range(len(st.session_state.test_suite.test_cases)),
            format_func=lambda x: f"Test #{x + 1}: {st.session_state.test_suite.test_cases[x].test_title}",
            default=[0] if st.session_state.test_suite.test_cases else []
        )

        execute_button = st.button("▶️ Execute Selected Tests", use_container_width=True, type="primary")

        if execute_button and selected_tests:
            st.session_state.execution_results = []

            progress_bar = st.progress(0)
            status_text = st.empty()

            for idx, test_idx in enumerate(selected_tests):
                test_case = st.session_state.test_suite.test_cases[test_idx]

                status_text.markdown(f"**Executing:** {test_case.test_title}")

                with st.expander(f"Executing Test #{test_idx + 1}: {test_case.test_title}", expanded=True):
                    st.markdown(f"**Description:** {test_case.description}")
                    st.markdown("**Test Steps:**")
                    st.code(test_case.test_steps, language="text")

                    try:
                        with st.spinner("🌐 Launching browser and executing test..."):
                            execution_result = async_runner.run(
                                execute_the_test_case_using_browser_use(test_case)
                            )

                        st.success("✅ Test execution completed!")
                        st.markdown("**Execution Result:**")
                        st.code(execution_result.structured_output, language="python")

                        st.session_state.execution_results.append({
                            "test_index": test_idx,
                            "test_title": test_case.test_title,
                            "status": "passed",
                            "result": execution_result.final_result(),
                            "timestamp": datetime.now().isoformat()
                        })

                    except Exception as e:
                        st.error(f"❌ Test execution failed: {str(e)}")
                        st.exception(e)
                        st.session_state.execution_results.append({
                            "test_index": test_idx,
                            "test_title": test_case.test_title,
                            "status": "failed",
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        })

                progress_bar.progress((idx + 1) / len(selected_tests))

            status_text.markdown("**✅ All selected tests executed!**")
            st.balloons()

# Tab 3: Results & Reports
with tab3:
    st.header("Results & Reports")
    st.markdown("View comprehensive test execution results and generate reports.")

    if not st.session_state.execution_results:
        st.info("ℹ️ No test execution results yet. Execute tests to see results here.")
    else:
        # Summary metrics
        total_tests = len(st.session_state.execution_results)
        passed_tests = sum(1 for r in st.session_state.execution_results if r["status"] == "passed")
        failed_tests = total_tests - passed_tests

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Tests", total_tests)
        col2.metric("Passed", passed_tests, delta=passed_tests if passed_tests > 0 else None, delta_color="normal")
        col3.metric("Failed", failed_tests, delta=failed_tests if failed_tests > 0 else None, delta_color="inverse")

        st.markdown("---")

        # Detailed results
        st.subheader("Detailed Results")

        for result in st.session_state.execution_results:
            status_icon = "✅" if result["status"] == "passed" else "❌"

            with st.expander(f"{status_icon} {result['test_title']} - {result['status'].upper()}"):
                st.markdown(f"**Test Index:** #{result['test_index'] + 1}")
                st.markdown(f"**Timestamp:** {result['timestamp']}")

                if result["status"] == "passed":
                    st.markdown("**Result:**")
                    st.code(result.get("result", "No result available"), language="python")
                else:
                    st.markdown("**Error:**")
                    st.error(result.get("error", "Unknown error"))

        # Export results
        st.markdown("---")
        st.subheader("Export Results")

        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                label="📥 Download Results (JSON)",
                data=json.dumps({"test_results": st.session_state.execution_results}, indent=4),
                file_name=f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

        with col2:
            # Generate simple text report
            report = f"""Test Execution Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Summary:
--------
Total Tests: {total_tests}
Passed: {passed_tests}
Failed: {failed_tests}
Success Rate: {(passed_tests / total_tests * 100):.1f}%

Detailed Results:
----------------
"""
            for result in st.session_state.execution_results:
                report += f"\n{result['test_title']}\n"
                report += f"Status: {result['status'].upper()}\n"
                report += f"Timestamp: {result['timestamp']}\n"
                report += "-" * 50 + "\n"

            st.download_button(
                label="📄 Download Report (TXT)",
                data=report,
                file_name=f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>AI Test Automation Suite | Powered by Playwright & LLM</div>",
    unsafe_allow_html=True
)