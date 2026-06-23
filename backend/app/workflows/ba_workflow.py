# app/workflows/ba_workflow.py

from app.agents.requirement_agent import run as requirement_agent
from app.agents.story_agent import run as story_agent
from app.agents.testcase_agent import run as testcase_agent
from app.agents.review_agent import run as review_agent

async def execute(document_text):

    requirements = await requirement_agent(
        document_text
    )

    stories = await story_agent(
        requirements
    )

    test_cases = await testcase_agent(
        stories
    )

    review = await review_agent(
        requirements,
        stories,
        test_cases
    )

    return {
        "requirements": requirements,
        "stories": stories,
        "test_cases": test_cases,
        "review": review
    }