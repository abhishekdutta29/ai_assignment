"""
Unit tests for Module 1: Knowledge Base (TripleStore, KnowledgeGraph, EntityIndex)
"""

import pytest
from src.extractor import Triple
from src.kb import KnowledgeBase, TripleStore, KnowledgeGraph, EntityIndex, levenshtein_distance, string_similarity

def test_levenshtein_distance():
    assert levenshtein_distance("kitten", "sitting") == 3
    assert levenshtein_distance("CS101", "CS101") == 0
    assert levenshtein_distance("AI", "AI201") == 3
    assert levenshtein_distance("Machne Learnng", "Machine Learning") == 2

def test_string_similarity():
    sim_exact = string_similarity("Artificial Intelligence", "Artificial Intelligence")
    assert sim_exact == 1.0
    sim_typo = string_similarity("Machne Learnng", "Machine Learning")
    assert sim_typo > 0.85

def test_entity_index_aliasing():
    index = EntityIndex()
    res_ai = index.resolve_entity("ai")
    assert res_ai is not None
    assert res_ai[0] == "AI201"

    res_ml = index.resolve_entity("machine learning")
    assert res_ml is not None
    assert res_ml[0] == "AI301"

    res_fuzzy = index.resolve_entity("Machne Learnng", fuzzy=True)
    assert res_fuzzy is not None
    assert res_fuzzy[0] == "AI301"

def test_triple_store_indexed_find():
    ts = TripleStore()
    t1 = Triple("AI201", "credits", "4", 10, "R04", "AI201 carries 4 credits.")
    t2 = Triple("AI201", "taught_by", "Prof. Alan Turing", 11, "R02", "AI201 is taught by Prof. Alan Turing.")
    ts.add(t1)
    ts.add(t2)

    assert len(ts.find(subject="AI201")) == 2
    assert len(ts.find(predicate="credits")) == 1
    assert ts.find(subject="AI201", predicate="credits")[0].object == "4"

def test_knowledge_graph_traversal():
    kg = KnowledgeGraph()
    t1 = Triple("AI401", "prerequisite", "AI301", 1, "R01", "")
    t2 = Triple("AI301", "prerequisite", "AI201", 2, "R01", "")
    t3 = Triple("AI201", "prerequisite", "CS102", 3, "R01", "")
    kg.add_edge("AI401", "AI301", "prerequisite", t1)
    kg.add_edge("AI301", "AI201", "prerequisite", t2)
    kg.add_edge("AI201", "CS102", "prerequisite", t3)

    deps, edges, steps = kg.find_transitive_dependencies("AI401", "prerequisite")
    assert deps == ["AI301", "AI201", "CS102"]

    reachable, path, reason = kg.check_reachability("CS102", "AI401", "prerequisite")
    assert reachable is True
    assert len(path) == 3
