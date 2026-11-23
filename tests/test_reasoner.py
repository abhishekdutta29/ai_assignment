"""
Unit tests for Module 2: Symbolic Reasoning Engine (All 5 Techniques)
"""

import pytest
from src.extractor import DocumentExtractor
from src.kb import KnowledgeBase
from src.question_parser import QuestionParser
from src.reasoner import ReasoningEngine
from src.inference_rules import StudentProfile

@pytest.fixture
def populated_kb():
    sample_text = """
CS101 is Introduction to Programming.
CS101 carries 4 credits.
CS101 is offered in Semester 1.
CS101 is taught by Dr. Ada Lovelace.

CS102 is Data Structures and Algorithms.
CS102 carries 4 credits.
CS102 is offered in Semester 2.
CS102 requires CS101.
CS102 is taught by Dr. Ada Lovelace.

AI201 is Artificial Intelligence.
AI201 carries 4 credits.
AI201 is offered in Semester 4.
AI201 requires CS102.
AI201 is taught by Prof. Alan Turing.

The minimum attendance requirement is 75%.
The Academic probation threshold is 2.0 CGPA.
The Dean's Honour List threshold is 3.75 CGPA.
"""
    extractor = DocumentExtractor()
    res = extractor.extract_from_text(sample_text)
    kb = KnowledgeBase()
    kb.populate(res)
    return kb

def test_technique1_direct_lookup(populated_kb):
    parser = QuestionParser(populated_kb.entity_index)
    reasoner = ReasoningEngine(populated_kb)

    q = parser.parse("Who teaches CS101?")
    res = reasoner.reason(q)
    assert res.status == "SUCCESS"
    assert res.trace.technique_name == "Direct Triple Store Lookup"
    triples = res.answer_payload["triples"]
    assert any("Ada Lovelace" in t["object"] for t in triples)

def test_technique2_transitive_chain(populated_kb):
    parser = QuestionParser(populated_kb.entity_index)
    reasoner = ReasoningEngine(populated_kb)

    q = parser.parse("What are all prerequisites of AI201?")
    res = reasoner.reason(q)
    assert res.status == "SUCCESS"
    assert "Graph Search" in res.trace.technique_name
    prereqs = res.answer_payload["prerequisites"]
    assert "CS102" in prereqs
    assert "CS101" in prereqs

def test_technique2_reachability(populated_kb):
    parser = QuestionParser(populated_kb.entity_index)
    reasoner = ReasoningEngine(populated_kb)

    q = parser.parse("Is CS101 required before AI201?")
    res = reasoner.reason(q)
    assert res.status == "SUCCESS"
    assert res.answer_payload["is_reachable"] is True

def test_technique3_forward_chaining(populated_kb):
    parser = QuestionParser(populated_kb.entity_index)
    reasoner = ReasoningEngine(populated_kb)

    profile = StudentProfile(completed_courses=["CS101", "CS102"], attendance=85.0, cgpa=3.9)
    q = parser.parse("Is the student eligible for AI201?")
    res = reasoner.reason(q, profile=profile)
    assert res.status == "SUCCESS"
    assert res.answer_payload["eligible"] is True

def test_technique4_backward_chaining(populated_kb):
    parser = QuestionParser(populated_kb.entity_index)
    reasoner = ReasoningEngine(populated_kb)

    profile = StudentProfile(completed_courses=["CS101"], attendance=60.0)
    q = parser.parse("Why is student barred from exam?")
    res = reasoner.reason(q, profile=profile)
    assert res.status == "SUCCESS"
    assert res.trace.proof_tree is not None
    assert res.trace.proof_tree["status"] == "PROVED"

def test_technique5_aggregations(populated_kb):
    parser = QuestionParser(populated_kb.entity_index)
    reasoner = ReasoningEngine(populated_kb)

    q = parser.parse("List all courses in Semester 1")
    res = reasoner.reason(q)
    assert res.status == "SUCCESS"
    assert "CS101" in res.answer_payload["courses"]
