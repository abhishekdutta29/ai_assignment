"""
Unit tests for Module 3: Quantitative Evaluator and Benchmark Harness
"""

import pytest
import os
import json
from src.extractor import DocumentExtractor
from src.kb import KnowledgeBase
from src.evaluator import BenchmarkEvaluator

@pytest.fixture
def evaluator():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    handbook_path = os.path.join(base_dir, "sample_data", "handbook.txt")
    text = DocumentExtractor.extract_text_from_file(handbook_path)
    extractor = DocumentExtractor()
    res = extractor.extract_from_text(text)
    kb = KnowledgeBase()
    kb.populate(res)
    return BenchmarkEvaluator(kb)

def test_full_evaluation_run(evaluator):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_file = os.path.join(base_dir, "sample_data", "test_questions.json")
    with open(test_file, "r", encoding="utf-8") as f:
        questions = json.load(f)

    report = evaluator.evaluate(questions, run_ablations=True)
    assert report.total_questions >= 40
    assert report.accuracy >= 95.0
    assert report.precision >= 95.0
    assert report.recall >= 95.0
    assert report.rejection_correctness >= 95.0

def test_ablation_effects(evaluator):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_file = os.path.join(base_dir, "sample_data", "test_questions.json")
    with open(test_file, "r", encoding="utf-8") as f:
        questions = json.load(f)

    report = evaluator.evaluate(questions, run_ablations=True)
    full_acc = report.ablation_results["Full System"]["accuracy"]
    rules_off_acc = report.ablation_results["Inference Rules OFF"]["accuracy"]
    # Deactivating inference rules must demonstrably lower the score
    assert full_acc > rules_off_acc
