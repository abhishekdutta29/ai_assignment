"""
KnowledgeLens - Module 2: Symbolic Question Analysis and Parsing
Performs rule-based question classification, deterministic entity linking via 
alias tables and Levenshtein edit distance, and hand-built relation lexicon mapping.
Strictly NO NLP libraries, word embeddings, or statistical parsers.
"""

import re
from typing import List, Dict, Tuple, Any, Optional
from src.kb import EntityIndex, levenshtein_distance, string_similarity

class StructuredQuery:
    """Structured representation of a parsed user question."""
    def __init__(self,
                 qtype: str,
                 raw_question: str,
                 entities: List[str],
                 entity_resolutions: List[Dict[str, Any]],
                 predicate: Optional[str] = None,
                 constraints: Optional[Dict[str, Any]] = None,
                 intent_description: str = ""):
        self.qtype = qtype
        self.raw_question = raw_question
        self.entities = entities
        self.entity_resolutions = entity_resolutions
        self.predicate = predicate
        self.constraints = constraints or {}
        self.intent_description = intent_description

    def to_dict(self) -> Dict[str, Any]:
        return {
            "qtype": self.qtype,
            "raw_question": self.raw_question,
            "entities": self.entities,
            "entity_resolutions": self.entity_resolutions,
            "predicate": self.predicate,
            "constraints": self.constraints,
            "intent_description": self.intent_description
        }


# Hand-built relation lexicon mapping keywords/phrases to symbolic predicates
RELATION_LEXICON: Dict[str, List[str]] = {
    "minimum_requirement": [
        "minimum attendance", "attendance requirement", "pass mark", "passing mark", 
        "pass marks", "minimum pass", "minimum requirement"
    ],
    "prerequisite": [
        "prerequisite", "prerequisites", "prereq", "prereqs", "prereqisite", 
        "requires", "required before", "needs before", "need before"
    ],
    "taught_by": [
        "taught by", "instructor", "instructed by", "professor", "lecturer", 
        "teacher", "who teaches", "who is teaching", "instructs"
    ],
    "teaches": [
        "teaches", "instructs", "courses taught"
    ],
    "degree_credits": [
        "degree credits", "programme credits", "total credits required", "credits to graduate", 
        "credits for bsc", "require 120 credits"
    ],
    "credits": [
        "how many credits", "carries how many credits", "credit hours", "points", "worth", "credits", "credit"
    ],
    "offered_in": [
        "offered in", "semester", "term", "runs in", "scheduled in", "when offered"
    ],
    "has_title": [
        "full name", "called", "stand for", "stands for", "name of"
    ],
    "department": [
        "department", "dept", "offered by", "which department"
    ],
    "belongs_to": [
        "belongs to", "school", "faculty", "part of"
    ],
    "assessment_weight": [
        "assessment", "weight", "weightage", "midterm", "final exam", "percentage"
    ],
    "deadline": [
        "deadline", "due date", "starts on", "due on", "scheduled date", "when is", "date of", "starts"
    ],
    "threshold": [
        "threshold", "probation", "dean's list", "deans list", "grade a", "grade b", "grade c", "grade d"
    ],
    "course_load": [
        "course load", "maximum credits", "minimum credits", "max load", "min load"
    ],
    "is_a_branch_of": [
        "branch of", "branch", "subfield of"
    ],
    "is_part_of": [
        "part of", "subset of"
    ],
    "purpose": [
        "helps", "purpose of", "what does it do", "function of"
    ],
    "definition": [
        "what is", "define", "definition of", "explain", "meaning of"
    ],
    "eligibility": [
        "eligible", "eligibility", "can take", "allowed to register", "qualified", "qualify", "barred"
    ]
}


class QuestionParser:
    """
    Symbolic question processor translating natural language questions into 
    StructuredQuery objects without any statistical NLP or ML tools.
    """
    def __init__(self, entity_index: EntityIndex):
        self.entity_index = entity_index

    def detect_relation(self, question: str) -> Optional[str]:
        """Detects symbolic relation using hand-built lexicon and phrase matching."""
        q_lower = question.lower()
        
        # Check specific phrase matches in order of specificity
        for relation, trigger_phrases in RELATION_LEXICON.items():
            for phrase in trigger_phrases:
                # Word boundary search
                pattern = r"\b" + re.escape(phrase) + r"\b"
                if re.search(pattern, q_lower):
                    return relation

        return None

    def extract_and_link_entities(self, question: str, fuzzy: bool = True) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Extracts entity candidates from question tokens and links them to canonical KB entities.
        Uses exact course code regex, canonical matches, alias lookups, and Levenshtein distance.
        """
        linked_entities: List[str] = []
        resolutions: List[Dict[str, Any]] = []
        seen_canonicals: Set[str] = set()

        # 1. Regex pass for course codes: e.g. CS101, MAT 202, AI-301
        code_matches = re.findall(r"\b([A-Za-z]{2,4}\s*-?\s*\d{3})\b", question)
        for code in code_matches:
            normalized_code = re.sub(r"[\s\-]+", "", code).upper()
            res = self.entity_index.resolve_entity(normalized_code, fuzzy=fuzzy)
            if res:
                canon, conf, method = res
                if canon not in seen_canonicals:
                    seen_canonicals.add(canon)
                    linked_entities.append(canon)
                    resolutions.append({
                        "mention": code,
                        "canonical": canon,
                        "confidence": conf,
                        "method": method
                    })

        # 2. Extract potential n-gram candidate phrases (1 to 4 words)
        clean_q = re.sub(r"[^\w\s\.\-]", " ", question)
        words = clean_q.split()

        stop_words = {
            "what", "is", "the", "are", "of", "in", "for", "to", "a", "an", "who", "which",
            "how", "many", "does", "do", "can", "student", "take", "all", "and", "or",
            "required", "before", "after", "by", "from", "on", "at", "has", "have", "list",
            "teaches", "taught", "instructor", "credits", "credit", "prerequisite", "prerequisites",
            "require", "requires", "offered", "runs", "carries", "belongs", "department"
        }

        # Check multi-word spans first (descending length)
        for n in range(4, 0, -1):
            for i in range(len(words) - n + 1):
                span = " ".join(words[i:i+n]).strip()
                if not span or span.lower() in stop_words:
                    continue

                res = self.entity_index.resolve_entity(span, fuzzy=fuzzy, threshold=0.72)
                if res:
                    canon, conf, method = res
                    if canon not in seen_canonicals:
                        seen_canonicals.add(canon)
                        linked_entities.append(canon)
                        resolutions.append({
                            "mention": span,
                            "canonical": canon,
                            "confidence": conf,
                            "method": method
                        })

        # Sort resolutions: Exact matches first, then by highest confidence
        method_priority = {"EXACT_CANONICAL": 3, "EXACT_ALIAS": 3, "SUBSTRING_MATCH": 2, "FUZZY_LEVENSHTEIN": 1}
        resolutions.sort(key=lambda r: (method_priority.get(r.get("method"), 0), r.get("confidence", 0)), reverse=True)
        
        # Deduplicate linked_entities maintaining sorted order
        ordered_entities = []
        for r in resolutions:
            c = r["canonical"]
            if c not in ordered_entities:
                ordered_entities.append(c)

        return ordered_entities, resolutions

    def parse(self, question: str, fuzzy: bool = True) -> StructuredQuery:
        """
        Parses question and builds a StructuredQuery object with detected question type.
        """
        q_clean = question.strip()
        q_lower = q_clean.lower()

        # 1. Detect Relation
        detected_relation = self.detect_relation(q_clean)

        # 2. Extract and link entities
        entities, resolutions = self.extract_and_link_entities(q_clean, fuzzy=fuzzy)

        # 3. Classify question type via symbolic heuristic rules
        qtype = "FACT_LOOKUP"
        intent = "Direct fact retrieval"
        constraints: Dict[str, Any] = {}

        # Rule T1: Compare questions
        if "compare" in q_lower or "which has more" in q_lower or "has more credits" in q_lower or "difference between" in q_lower:
            qtype = "COMPARISON"
            intent = "Symbolic comparison between two entities"

        # Rule T2: Transitive chain questions
        elif any(phrase in q_lower for phrase in ["all prerequisites", "prerequisite chain", "full prerequisites", "everything required", "all the prerequisites"]):
            qtype = "TRANSITIVE_CHAIN"
            intent = "BFS/DFS transitive traversal of dependency graph"

        # Rule T3: Reachability queries
        elif (("required before" in q_lower or "prerequisite before" in q_lower or "needed before" in q_lower or "lead to" in q_lower) and len(entities) >= 2) or \
             ("is" in q_lower and "reachable" in q_lower):
            qtype = "REACHABILITY"
            intent = "Shortest path / reachability verification on Knowledge Graph"

        # Rule T4: Aggregation - Sum
        elif any(term in q_lower for term in ["total credit", "sum of credit", "total credit count", "sum of credits"]):
            qtype = "AGGREGATION_SUM"
            intent = "Aggregation sum of credit values matching constraints"

        # Rule T5: Why / Proof questions
        elif q_lower.startswith("why") or "prove" in q_lower or "reason for" in q_lower:
            qtype = "BACKWARD_PROOF"
            intent = "Goal-driven backward chaining to construct proof tree"

        # Rule T6: Student state / Eligibility (Forward chaining) - requires student reference
        elif ("student" in q_lower or "profile" in q_lower or "can i" in q_lower) and any(term in q_lower for term in ["eligible", "qualify", "probation", "barred", "can the student", "is the student", "take examination"]):
            qtype = "FORWARD_INFERENCE"
            intent = "Forward chaining Horn clauses against factual Student Profile"

        # Rule T7: Aggregation - Count
        elif q_lower.startswith("how many") or "count" in q_lower or "number of" in q_lower:
            # Check if count or credits
            if detected_relation in ["credits", "degree_credits"] and (entities or "bsc" in q_lower or "degree" in q_lower):
                qtype = "FACT_LOOKUP"
                intent = "Lookup single entity credit value"
            else:
                qtype = "AGGREGATION_COUNT"
                intent = "Aggregation count query over Knowledge Base triples"

        # Rule T8: Filter / List queries
        elif q_lower.startswith("list") or "which courses" in q_lower or "show all" in q_lower:
            qtype = "FILTER_LIST"
            intent = "Filter triples satisfying constraints and list results"

        # Extract semester constraint if present
        sem_match = re.search(r"\bSemester\s*(\d+)\b", q_clean, re.IGNORECASE)
        if sem_match:
            constraints["semester"] = f"Semester {sem_match.group(1)}"

        # Concept definition relations require at least one identified entity
        if not entities and detected_relation in ["definition", "purpose", "is_a_branch_of", "is_part_of"]:
            detected_relation = None

        # If no entities and no relation detected, flag as UNANSWERABLE
        if not entities and not detected_relation:
            qtype = "UNANSWERABLE"
            intent = "Question does not match any known entities or domain relations"

        return StructuredQuery(
            qtype=qtype,
            raw_question=q_clean,
            entities=entities,
            entity_resolutions=resolutions,
            predicate=detected_relation,
            constraints=constraints,
            intent_description=intent
        )
