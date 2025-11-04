from browser_use import BrowserProfile
from browser_use.agent.service import Agent

from playwright_llm_integration.prompts import TEST_SUITE_GENERATOR_PROMPT, BROWSER_USE_TEST_EXECUTOR_TASK_PROMPT, \
    PAGE_EXPLORATION_PROMPT_TEMPLATE
from playwright_llm_integration.models import TestSuite, TestCase
from playwright_llm_integration.tools import browser_use_llm
from playwright_llm_integration.utils import instructor_patched_google_llm_client, browser_use_google_llm


async def test_suite_generation_agent(base_url: str, application_description: str):
    test_suite = await instructor_patched_google_llm_client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": TEST_SUITE_GENERATOR_PROMPT.format(
                    application_description=application_description
                )
            },
            {
                "role": "user",
                "content": f"The upstream llm has extracted the page elements from {base_url}. Based on this, generate a comprehensive test suite."
                           f"Apply best practices for web application testing. Ensure the test cases cover functionality, usability, edge cases, and error handling"
            }
        ],
        response_model=TestSuite,
        generation_config={
            "temperature": 0.0,
            # "max_tokens": 1000,
            # "top_p": 1,
            # "top_k": 32,
        }
    )


    return test_suite


async def execute_the_test_case_using_browser_use(test_case: TestCase):
    browser_profile = BrowserProfile(
        minimum_wait_page_load_time=0.1,
        wait_between_actions=0.1,
        headless=False,
        is_local=True
    )

    test_execution_task = BROWSER_USE_TEST_EXECUTOR_TASK_PROMPT.format(test_case=test_case.model_dump_json())
    try:
        test_execution_agent = Agent(
            task=test_execution_task,
            llm=browser_use_google_llm,
            browser_profile=browser_profile,
            # browser=browser,
            use_vision=True
        )
        test_execution_result = await test_execution_agent.run()
    except Exception as e:
        test_execution_result = f"Error during test execution: {str(e)}"


    return test_execution_result




async def page_exploration_agent(base_url: str, description: str) :
    navigation_task = PAGE_EXPLORATION_PROMPT_TEMPLATE.format(base_url=base_url)

    if description:
        navigation_task += f"\n\nThe application is described as: {description}"

    # browser = Browser() # TODO - configure as needed
    browser_profile = BrowserProfile(
        minimum_wait_page_load_time=0.1,
        wait_between_actions=0.1,
        headless=True,
        is_local=True
    )
    exploration_agent = Agent(
        task=navigation_task,
        llm=browser_use_llm,
        browser_profile=browser_profile,
        # browser=browser,
        use_vision=True
    )
    exploration_result = await exploration_agent.run()
    return exploration_result

async def test_orchestration_agent(base_url: str, description: str = ""):
    ...



if __name__ == '__main__':
    ...
