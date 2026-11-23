"""
Unit tests for Module 1: Document Processing and Information Extraction
"""

import pytest
from src.extractor import DocumentExtractor, Triple, get_default_extraction_rules

def test_sentence_splitting():
    extractor = DocumentExtractor()
    text = "CS101 carries 4 credits. CS101 is Introduction to Programming!\nCS102 requires CS101."
    sentences = extractor.split_into_sentences(text)
    assert len(sentences) == 3
    assert sentences[0][1] == "CS101 carries 4 credits"
    assert sentences[1][1] == "CS101 is Introduction to Programming"
    assert sentences[2][1] == "CS102 requires CS101"

def test_prerequisite_extraction():
    extractor = DocumentExtractor()
    text = "AI301 requires AI201. AI401 has prerequisite AI301."
    res = extractor.extract_from_text(text)
    triples = res["triples"]
    prereq_triples = [t for t in triples if t.predicate == "prerequisite"]
    assert len(prereq_triples) == 2
    assert any(t.subject == "AI301" and t.object == "AI201" for t in prereq_triples)
    assert any(t.subject == "AI401" and t.object == "AI301" for t in prereq_triples)

def test_taught_by_and_teaches():
    extractor = DocumentExtractor()
    text = "CS101 is taught by Dr. Ada Lovelace."
    res = extractor.extract_from_text(text)
    triples = res["triples"]
    assert any(t.subject == "CS101" and t.predicate == "taught_by" and "Ada Lovelace" in t.object for t in triples)
    # Reciprocal teaches triple
    assert any("Ada Lovelace" in t.subject and t.predicate == "teaches" and t.object == "CS101" for t in triples)

def test_markdown_table_parsing():
    extractor = DocumentExtractor()
    table_text = """
| Code | Title | Credits | Semester | Prerequisite | Instructor | Department |
| CS101 | Introduction to Programming | 4 | Semester 1 | None | Dr. Ada Lovelace | Computer Science |
| CS102 | Data Structures | 4 | Semester 2 | CS101 | Dr. Ada Lovelace | Computer Science |
"""
    res = extractor.extract_from_text(table_text)
    triples = res["triples"]
    assert any(t.subject == "CS101" and t.predicate == "credits" and t.object == "4" for t in triples)
    assert any(t.subject == "CS102" and t.predicate == "prerequisite" and t.object == "CS101" for t in triples)
    assert any(t.subject == "CS101" and t.predicate == "offered_in" and t.object == "Semester 1" for t in triples)

def test_unparsed_sentences_tracking():
    extractor = DocumentExtractor()
    text = "CS101 carries 4 credits.\nThis is an arbitrary English prose comment without rules."
    res = extractor.extract_from_text(text)
    assert res["parsed_sentences_count"] >= 1
    assert len(res["unparsed_sentences"]) >= 1
    assert any("arbitrary English prose" in s["text"] for s in res["unparsed_sentences"])
