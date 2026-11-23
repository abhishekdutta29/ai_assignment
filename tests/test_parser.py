"""
Unit tests for Module 2: Symbolic Question Parser
"""

import pytest
from src.kb import EntityIndex
from src.question_parser import QuestionParser

@pytest.fixture
def parser():
    index = EntityIndex()
    index.register_course("AI201", "Artificial Intelligence")
    index.register_course("AI301", "Machine Learning")
    index.register_course("AI401", "Deep Learning")
    index.register_course("CS101", "Introduction to Programming")
    index.register_course("CS102", "Data Structures and Algorithms")
    return QuestionParser(index)

def test_fact_lookup_classification(parser):
    q = parser.parse("Who teaches Artificial Intelligence?")
    assert q.qtype == "FACT_LOOKUP"
    assert q.predicate == "taught_by"
    assert "AI201" in q.entities

def test_transitive_classification(parser):
    q = parser.parse("What are all prerequisites of Deep Learning?")
    assert q.qtype == "TRANSITIVE_CHAIN"
    assert "AI401" in q.entities

def test_reachability_classification(parser):
    q = parser.parse("Is CS101 required before Machine Learning?")
    assert q.qtype == "REACHABILITY"
    assert "CS101" in q.entities
    assert "AI301" in q.entities

def test_forward_chaining_classification(parser):
    q = parser.parse("Is the student eligible for AI401?")
    assert q.qtype == "FORWARD_INFERENCE"

def test_backward_chaining_classification(parser):
    q = parser.parse("Why is student barred from exam?")
    assert q.qtype == "BACKWARD_PROOF"

def test_comparison_classification(parser):
    q = parser.parse("Which course has more credits, AI201 or CS101?")
    assert q.qtype == "COMPARISON"
    assert len(q.entities) >= 2

def test_unanswerable_classification(parser):
    q = parser.parse("What is the cafeteria lunch menu for Friday?")
    assert q.qtype == "UNANSWERABLE"
