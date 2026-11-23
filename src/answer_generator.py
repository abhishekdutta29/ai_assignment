"""
KnowledgeLens - Module 3: Template-Based Answer Generation
Deterministic natural language synthesis using symbolic templates without LLMs or statistical NLG.
"""

from typing import Dict, Any, List
from src.reasoner import ReasoningResult
from src.question_parser import StructuredQuery

class AnswerGenerator:
    """Generates precise, deterministic natural language answers from reasoning results."""

    @staticmethod
    def generate(result: ReasoningResult, query: StructuredQuery) -> Dict[str, Any]:
        """Translates symbolic reasoning output into human-readable text and evidence lists."""
        trace_dict = result.trace.to_dict()
        evidence_triples = trace_dict.get("supporting_triples", [])

        if result.status == "NOT_FOUND":
            base_msg = "Not found in the knowledge base."
            if result.closest_suggestions:
                sugg_str = ", ".join(result.closest_suggestions[:5])
                full_text = f"{base_msg} Closest known entities in the domain: {sugg_str}."
            else:
                full_text = base_msg
            return {
                "answer_text": full_text,
                "status": "NOT_FOUND",
                "evidence": [],
                "trace": trace_dict
            }

        payload = result.answer_payload
        answer_text = ""

        # 1. Transitive prerequisite chain
        if query.qtype == "TRANSITIVE_CHAIN":
            target = payload.get("target_course", "the course")
            prereqs = payload.get("prerequisites", [])
            count = payload.get("chain_length", 0)
            if count == 0:
                answer_text = f"{target} has no prerequisites recorded in the curriculum."
            else:
                chain_str = " -> ".join(prereqs)
                answer_text = f"The complete prerequisite chain for {target} requires {count} course(s): {chain_str}."

        # 2. Reachability verification
        elif query.qtype == "REACHABILITY":
            answer_text = payload.get("message", "Reachability evaluation completed.")

        # 3. Forward Chaining inference
        elif query.qtype == "FORWARD_INFERENCE":
            if "explanation" in payload:
                answer_text = payload["explanation"]
            elif "eligible_courses" in payload:
                courses = payload["eligible_courses"]
                if courses:
                    answer_text = f"Based on completed prerequisites, the student is currently eligible to register for {len(courses)} course(s): {', '.join(courses)}."
                else:
                    answer_text = "The student is not currently eligible for any additional courses."

        # 4. Backward Chaining proof
        elif query.qtype == "BACKWARD_PROOF":
            tree = payload.get("proof_tree", {})
            conclusion = tree.get("conclusion", "Proof resolved.")
            status = tree.get("status", "RESOLVED")
            rule = tree.get("rule_applied", "")
            subgoals = tree.get("subgoals", [])
            facts = [sg.get("fact") for sg in subgoals if "fact" in sg]
            facts_str = " | ".join(facts) if facts else ""
            answer_text = f"Proof Status: [{status}]. {conclusion} (Applied Rule: {rule}). Facts verified: {facts_str}."

        # 5. Aggregation - Sum
        elif query.qtype == "AGGREGATION_SUM":
            sem = payload.get("semester", "")
            tot = payload.get("total_credits", 0)
            courses = payload.get("courses", [])
            answer_text = f"The total credit load for {sem} is {tot} credits (comprising: {', '.join(courses)})."

        # 6. Aggregation - Count & Filter
        elif query.qtype in ["AGGREGATION_COUNT", "FILTER_LIST"]:
            if "courses" in payload:
                courses = payload.get("courses", [])
                context = payload.get("semester") or payload.get("instructor") or payload.get("department") or ""
                answer_text = f"Found {len(courses)} course(s) for {context}: {', '.join(courses)}."
            elif "count" in payload:
                answer_text = f"Total count: {payload.get('count')}."
            else:
                answer_text = "Aggregation query successfully resolved."

        # 7. Comparison
        elif query.qtype == "COMPARISON":
            answer_text = payload.get("verdict", "Comparison evaluated.")

        # 8. Direct Triple Lookup
        else:
            triples = payload.get("triples", [])
            if not triples:
                answer_text = "Not found in the knowledge base."
            else:
                sentences = []
                for t in triples:
                    subj = t.get("subject", "")
                    pred = t.get("predicate", "")
                    obj = t.get("object", "")

                    if pred == "taught_by":
                        sentences.append(f"{subj} is taught by {obj}.")
                    elif pred == "teaches":
                        sentences.append(f"{subj} teaches {obj}.")
                    elif pred == "credits":
                        sentences.append(f"{subj} carries {obj} credits.")
                    elif pred == "prerequisite":
                        sentences.append(f"{subj} requires {obj} as a prerequisite.")
                    elif pred == "offered_in":
                        sentences.append(f"{subj} is offered in {obj}.")
                    elif pred == "has_title":
                        sentences.append(f"{subj} is {obj}.")
                    elif pred == "department":
                        sentences.append(f"{subj} belongs to the Department of {obj}.")
                    elif pred == "belongs_to":
                        sentences.append(f"{subj} belongs to the {obj}.")
                    elif pred == "deadline":
                        sentences.append(f"The deadline for {subj} is {obj}.")
                    elif pred == "minimum_requirement":
                        sentences.append(f"The minimum requirement for {subj} is {obj}.")
                    elif pred == "threshold":
                        sentences.append(f"The threshold for {subj} is {obj}.")
                    elif pred == "degree_credits":
                        sentences.append(f"{subj} requires {obj} credits to graduate.")
                    elif pred == "course_load":
                        sentences.append(f"The {subj} course load is {obj} credits.")
                    elif pred == "is_a_branch_of":
                        sentences.append(f"{subj} is a branch of {obj}.")
                    elif pred == "is_part_of":
                        sentences.append(f"{subj} is a part of {obj}.")
                    elif pred == "purpose":
                        sentences.append(f"{subj} helps {obj}.")
                    elif pred == "behavior":
                        sentences.append(f"{subj} {obj}.")
                    elif pred == "assessment_weight":
                        sentences.append(f"{subj} carries a weightage of {obj}.")
                    else:
                        sentences.append(f"{subj} {pred} {obj}.")
                answer_text = " ".join(sentences)

        return {
            "answer_text": answer_text,
            "status": "SUCCESS",
            "evidence": evidence_triples,
            "trace": trace_dict
        }
