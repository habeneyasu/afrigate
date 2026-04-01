"""Tests for core/graph.py — routing logic and graph compilation."""

import pytest
from langgraph.graph import END

from core.graph import _route, build_graph


class TestRoute:
    def test_accept_ends(self):
        assert _route({"evaluator_decision": "accept", "iteration": 0}) == END

    def test_ask_user_ends(self):
        assert _route({"evaluator_decision": "ask_user", "iteration": 1}) == END

    def test_retry_within_cap_routes_to_doc_intel(self):
        assert _route({"evaluator_decision": "retry", "iteration": 1}) == "doc_intel"

    def test_retry_at_cap_ends(self):
        assert _route({"evaluator_decision": "retry", "iteration": 3}) == END

    def test_retry_beyond_cap_ends(self):
        assert _route({"evaluator_decision": "retry", "iteration": 99}) == END

    def test_no_decision_ends(self):
        assert _route({"iteration": 0}) == END


class TestBuildGraph:
    def test_compiles(self):
        assert build_graph() is not None

    def test_is_invocable(self):
        assert callable(build_graph().invoke)
