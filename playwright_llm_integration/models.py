from enum import StrEnum

from pydantic import BaseModel, Field


class TestCase(BaseModel):
    test_case_id: str = Field(..., description="Unique identifier for the test case.")
    test_title: str = Field(..., description="Title of the test case.")
    description: str = Field(..., description="Detailed description of what the test case covers.")
    preconditions: str = Field(..., description="Any setup required before execution.")
    test_steps: str = Field(..., description="Step-by-step execution guide.")
    test_data: str = Field(..., description="Input values required for the test.")
    expected_result: str = Field(..., description="The anticipated outcome.")
    comments: str = Field(..., description="Additional notes or observations.")


class TestSuite(BaseModel):
    suite_id: str = Field(..., description="Unique identifier for the test suite.")
    suite_name: str = Field(..., description="Name of the test suite.")
    test_cases: list[TestCase] = Field(..., description="List of test cases included in the suite.")

class IntentEnum(StrEnum):
    RUN_TEST = "RUN_TEST"
    GENERATE_TEST_SUITE = "GENERATE_TEST_SUITE"
    EXPLORE_PAGE = "EXPLORE_PAGE"


class OrchestratorResponse(BaseModel):
    intent: IntentEnum = Field(..., description="Determined intent of the agent.")
    response: str = Field(..., description="Anticipated outcome.")

