"""
KnowledgeLens - Module 3: Quantitative Evaluator and Benchmark Harness
Evaluates system performance against gold standard questions.
Computes accuracy, precision, recall, F1, coverage, rejection rate, response latency,
breakdowns by question type and reasoning technique, and ablation studies.
"""

import json
import time
from typing import List, Dict, Any, Optional
from src.kb import KnowledgeBase
from src.question_parser import QuestionParser
from src.reasoner import ReasoningEngine
from src.answer_generator import AnswerGenerator
from src.inference_rules import StudentProfile

class EvaluationReport:
    """Stores full metrics, per-question logs, and ablation comparative data."""
    def __init__(self):
        self.total_questions: int = 0
        self.passed: int = 0
        self.failed: int = 0
        self.accuracy: float = 0.0
        self.precision: float = 0.0
        self.recall: float = 0.0
        self.f1: float = 0.0
        self.coverage: float = 0.0
        self.rejection_correctness: float = 0.0
        self.avg_response_time_ms: float = 0.0
        self.type_breakdown: Dict[str, Dict[str, Any]] = {}
        self.technique_breakdown: Dict[str, Dict[str, Any]] = {}
        self.error_analysis: Dict[str, int] = {
            "EXTRACTION_MISS": 0,
            "ENTITY_LINK_MISS": 0,
            "WRONG_RELATION": 0,
            "REASONING_GAP": 0,
            "NONE": 0
        }
        self.question_results: List[Dict[str, Any]] = []
        self.ablation_results: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_questions": self.total_questions,
            "passed": self.passed,
            "failed": self.failed,
            "accuracy": round(self.accuracy, 2),
            "precision": round(self.precision, 2),
            "recall": round(self.recall, 2),
            "f1": round(self.f1, 2),
            "coverage": round(self.coverage, 2),
            "rejection_correctness": round(self.rejection_correctness, 2),
            "avg_response_time_ms": round(self.avg_response_time_ms, 2),
            "type_breakdown": self.type_breakdown,
            "technique_breakdown": self.technique_breakdown,
            "error_analysis": self.error_analysis,
            "question_results": self.question_results,
            "ablation_results": self.ablation_results
        }


class BenchmarkEvaluator:
    """Runs automated benchmarks over knowledge base."""
    def __init__(self, kb: KnowledgeBase):
        self.kb = kb
        self.parser = QuestionParser(kb.entity_index)
        self.reasoner = ReasoningEngine(kb)

    def run_single(self, q_item: Dict[str, Any], fuzzy: bool = True, enable_rules: bool = True, profile: Optional[StudentProfile] = None) -> Dict[str, Any]:
        """Runs a single test question through the pipeline and scores it."""
        t_start = time.perf_counter()

        parsed_q = self.parser.parse(q_item["question"], fuzzy=fuzzy)
        reason_res = self.reasoner.reason(parsed_q, profile=profile, enable_rules=enable_rules)
        gen_res = AnswerGenerator.generate(reason_res, parsed_q)

        elapsed_ms = (time.perf_counter() - t_start) * 1000.0
        answer_text = gen_res["answer_text"]

        # Evaluate correctness against gold expectations
        gold_contains = q_item.get("gold_answer_contains", [])
        should_fail = q_item.get("should_fail", False)

        passed = False
        error_category = "NONE"

        if should_fail:
            # For adversarial / unanswerable questions, pass if the system gracefully reports not found
            if "not found in the knowledge base" in answer_text.lower():
                passed = True
            else:
                passed = False
                error_category = "REASONING_GAP"
        else:
            # Check if all required gold tokens are present in answer
            all_found = all(term.lower() in answer_text.lower() for term in gold_contains)
            if all_found and "not found" not in answer_text.lower():
                passed = True
            else:
                passed = False
                # Categorize error cause
                if not parsed_q.entities:
                    error_category = "ENTITY_LINK_MISS"
                elif not parsed_q.predicate and parsed_q.qtype == "FACT_LOOKUP":
                    error_category = "WRONG_RELATION"
                elif "not found" in answer_text.lower():
                    error_category = "EXTRACTION_MISS"
                else:
                    error_category = "REASONING_GAP"

        return {
            "id": q_item["id"],
            "question": q_item["question"],
            "category": q_item.get("category", "General"),
            "expected_type": q_item.get("expected_type", ""),
            "actual_type": parsed_q.qtype,
            "technique": reason_res.trace.technique_name,
            "gold_contains": gold_contains,
            "actual_answer": answer_text,
            "passed": passed,
            "error_category": error_category,
            "time_ms": round(elapsed_ms, 2),
            "trace_steps": reason_res.trace.steps,
            "evidence_count": len(gen_res["evidence"])
        }

    def evaluate(self, test_questions: List[Dict[str, Any]], run_ablations: bool = True) -> EvaluationReport:
        """Runs the entire benchmark test suite and returns full metrics."""
        report = EvaluationReport()
        report.total_questions = len(test_questions)

        total_time = 0.0
        true_positives = 0
        false_positives = 0
        false_negatives = 0
        true_negatives = 0

        unanswerable_total = 0
        unanswerable_correct = 0

        answerable_total = 0
        answerable_answered = 0

        default_profile = StudentProfile()

        for q_item in test_questions:
            res = self.run_single(q_item, fuzzy=True, enable_rules=True, profile=default_profile)
            report.question_results.append(res)

            total_time += res["time_ms"]
            is_unanswerable = q_item.get("should_fail", False)

            if is_unanswerable:
                unanswerable_total += 1
                if res["passed"]:
                    unanswerable_correct += 1
                    true_negatives += 1
                else:
                    false_positives += 1
            else:
                answerable_total += 1
                if res["passed"]:
                    true_positives += 1
                    answerable_answered += 1
                else:
                    false_negatives += 1

            if res["passed"]:
                report.passed += 1
            else:
                report.failed += 1
                report.error_analysis[res["error_category"]] = report.error_analysis.get(res["error_category"], 0) + 1

            # Type breakdown
            q_type = res["expected_type"] or res["actual_type"]
            if q_type not in report.type_breakdown:
                report.type_breakdown[q_type] = {"total": 0, "passed": 0, "failed": 0, "accuracy": 0.0}
            report.type_breakdown[q_type]["total"] += 1
            if res["passed"]:
                report.type_breakdown[q_type]["passed"] += 1
            else:
                report.type_breakdown[q_type]["failed"] += 1

            # Technique breakdown
            tech = res["technique"]
            if tech not in report.technique_breakdown:
                report.technique_breakdown[tech] = {"total": 0, "passed": 0, "failed": 0, "accuracy": 0.0}
            report.technique_breakdown[tech]["total"] += 1
            if res["passed"]:
                report.technique_breakdown[tech]["passed"] += 1
            else:
                report.technique_breakdown[tech]["failed"] += 1

        # Calculate metrics
        report.accuracy = (report.passed / max(1, report.total_questions)) * 100.0
        
        prec_denom = (true_positives + false_positives)
        report.precision = ((true_positives / prec_denom) * 100.0) if prec_denom > 0 else 0.0

        rec_denom = (true_positives + false_negatives)
        report.recall = ((true_positives / rec_denom) * 100.0) if rec_denom > 0 else 0.0

        if report.precision + report.recall > 0:
            report.f1 = (2 * report.precision * report.recall) / (report.precision + report.recall)
        else:
            report.f1 = 0.0

        report.coverage = ((answerable_answered / max(1, answerable_total)) * 100.0)
        report.rejection_correctness = ((unanswerable_correct / max(1, unanswerable_total)) * 100.0) if unanswerable_total > 0 else 100.0
        report.avg_response_time_ms = total_time / max(1, report.total_questions)

        # Finalize breakdowns
        for k, v in report.type_breakdown.items():
            v["accuracy"] = round((v["passed"] / max(1, v["total"])) * 100.0, 1)
        for k, v in report.technique_breakdown.items():
            v["accuracy"] = round((v["passed"] / max(1, v["total"])) * 100.0, 1)

        # Run Ablation experiments if requested
        if run_ablations:
            report.ablation_results = self._run_ablations(test_questions, report.accuracy)

        return report

    def _run_ablations(self, test_questions: List[Dict[str, Any]], baseline_acc: float) -> Dict[str, Any]:
        """Runs ablation benchmarks: Fuzzy OFF, Rules OFF."""
        # 1. Fuzzy matching OFF
        fuzzy_off_passed = 0
        for q in test_questions:
            res = self.run_single(q, fuzzy=False, enable_rules=True)
            if res["passed"]:
                fuzzy_off_passed += 1
        fuzzy_off_acc = (fuzzy_off_passed / max(1, len(test_questions))) * 100.0

        # 2. Inference rules OFF
        rules_off_passed = 0
        for q in test_questions:
            res = self.run_single(q, fuzzy=True, enable_rules=False)
            if res["passed"]:
                rules_off_passed += 1
        rules_off_acc = (rules_off_passed / max(1, len(test_questions))) * 100.0

        return {
            "Full System": {
                "accuracy": round(baseline_acc, 2),
                "delta": "+0.0%"
            },
            "Fuzzy Matching OFF": {
                "accuracy": round(fuzzy_off_acc, 2),
                "delta": f"-{round(baseline_acc - fuzzy_off_acc, 2)}%"
            },
            "Inference Rules OFF": {
                "accuracy": round(rules_off_acc, 2),
                "delta": f"-{round(baseline_acc - rules_off_acc, 2)}%"
            }
        }
