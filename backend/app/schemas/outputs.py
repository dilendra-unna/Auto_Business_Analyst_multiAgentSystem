from typing import List, Optional
from pydantic import BaseModel


class AcceptanceCriteria(BaseModel):
    id: str
    description: str


class UserStory(BaseModel):
    epic: str
    title: str
    story: str
    acceptance_criteria: List[AcceptanceCriteria]


class TestCase(BaseModel):
    type: str  # positive | negative | edge
    scenario: str
    expected_result: str


class ReviewFinding(BaseModel):
    category: str
    severity: str
    finding: str
    recommendation: str


class RequirementOutput(BaseModel):
    modules: list


class StoryOutput(BaseModel):
    stories: List[UserStory]


class TestCaseOutput(BaseModel):
    test_cases: List[TestCase]


class ReviewOutput(BaseModel):
    findings: List[ReviewFinding]


class WorkflowOutput(BaseModel):
    requirements: dict
    stories: StoryOutput
    test_cases: TestCaseOutput
    review: ReviewOutput