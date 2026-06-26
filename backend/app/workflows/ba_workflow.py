# app/workflows/ba_workflow.py
#
# LangGraph-based BA Copilot workflow.
#
# Graph:
#   START → extract_requirements → generate_stories → generate_test_cases → review_artifacts → END
#
# State flows through each node sequentially; each node reads from the
# previous node's output field and writes its own output field.

from typing import Any, Dict, Optional

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END

from app.agents.requirement_agent import run as run_requirements
from app.agents.story_agent import run as run_stories
from app.agents.testcase_agent import run as run_testcases
from app.agents.review_agent import run as run_review


# ── Shared workflow state ──────────────────────────────────────────────────────

class BAState(TypedDict):
    """Mutable state object passed between every node in the graph."""
    document_text: str
    requirements: Optional[Dict[str, Any]]
    stories: Optional[Dict[str, Any]]
    test_cases: Optional[Dict[str, Any]]
    review: Optional[Dict[str, Any]]


# ── Node functions ─────────────────────────────────────────────────────────────

async def extract_requirements(state: BAState) -> BAState:
    """Node 1 — Parse document text → structured requirements."""
    requirements = await run_requirements(state["document_text"])
    return {**state, "requirements": requirements}


async def generate_stories(state: BAState) -> BAState:
    """Node 2 — Convert requirements → Agile user stories."""
    stories = await run_stories(state["requirements"])
    return {**state, "stories": stories}


async def generate_test_cases(state: BAState) -> BAState:
    """Node 3 — Derive test cases from user stories."""
    test_cases = await run_testcases(state["stories"])
    return {**state, "test_cases": test_cases}


async def review_artifacts(state: BAState) -> BAState:
    """Node 4 — QA review of all artifacts and surface findings."""
    review = await run_review(
        state["requirements"],
        state["stories"],
        state["test_cases"],
    )
    return {**state, "review": review}


# ── Graph assembly ─────────────────────────────────────────────────────────────

def _build_graph() -> StateGraph:
    graph = StateGraph(BAState)

    graph.add_node("extract_requirements", extract_requirements)
    graph.add_node("generate_stories", generate_stories)
    graph.add_node("generate_test_cases", generate_test_cases)
    graph.add_node("review_artifacts", review_artifacts)

    graph.add_edge(START, "extract_requirements")
    graph.add_edge("extract_requirements", "generate_stories")
    graph.add_edge("generate_stories", "generate_test_cases")
    graph.add_edge("generate_test_cases", "review_artifacts")
    graph.add_edge("review_artifacts", END)

    return graph


# Compile once at import time — reused across all requests.
_workflow = _build_graph().compile()


# ── Public API ─────────────────────────────────────────────────────────────────

async def execute(document_text: str) -> Dict[str, Any]:
    """
    Run the full BA workflow for the given document text.

    Returns a dict with keys:
        requirements, stories, test_cases, review
    """
    initial_state: BAState = {
        "document_text": document_text,
        "requirements": None,
        "stories": None,
        "test_cases": None,
        "review": None,
    }

    final_state: BAState = await _workflow.ainvoke(initial_state)

    return {
        "requirements": final_state["requirements"],
        "stories": final_state["stories"],
        "test_cases": final_state["test_cases"],
        "review": final_state["review"],
    }
