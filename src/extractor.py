"""
KnowledgeLens - Module 1: Document Processing and Information Extraction
Symbolic, rule-based extraction system without any NLP or ML libraries.
"""

import re
import os
from typing import List, Dict, Tuple, Any, Optional

class Triple:
    """Represents a symbolic fact: (subject, predicate, object) with provenance."""
    def __init__(self, subject: str, predicate: str, obj: str, source_line: int, rule_id: str, raw_text: str):
        self.subject = subject.strip()
        self.predicate = predicate.strip()
        self.object = obj.strip()
        self.source_line = source_line
        self.rule_id = rule_id
        self.raw_text = raw_text.strip()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "source_line": self.source_line,
            "rule_id": self.rule_id,
            "raw_text": self.raw_text
        }

    def __repr__(self) -> str:
        return f"({self.subject}, {self.predicate}, {self.object}) [Line {self.source_line}, Rule {self.rule_id}]"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Triple):
            return False
        return (self.subject.lower() == other.subject.lower() and
                self.predicate.lower() == other.predicate.lower() and
                self.object.lower() == other.object.lower())

    def __hash__(self) -> int:
        return hash((self.subject.lower(), self.predicate.lower(), self.object.lower()))


class ExtractionRule:
    """A symbolic regex rule that extracts triples from text sentences."""
    def __init__(self, rule_id: str, pattern: str, predicate: str, 
                 subj_group: int, obj_group: int, description: str,
                 fixed_subject: Optional[str] = None, fixed_predicate: Optional[str] = None):
        self.rule_id = rule_id
        self.pattern = re.compile(pattern, re.IGNORECASE)
        self.predicate = predicate
        self.subj_group = subj_group
        self.obj_group = obj_group
        self.description = description
        self.fixed_subject = fixed_subject
        self.fixed_predicate = fixed_predicate


def get_default_extraction_rules() -> List[ExtractionRule]:
    """Returns the rule table with 14 classical symbolic extraction patterns."""
    return [
        ExtractionRule(
            rule_id="R01_PREREQ",
            pattern=r"\b([A-Z]{2,4}\s*\d{3})\b\s*(?:requires|has prerequisite|prerequisite is|needs)\s*\b([A-Z]{2,4}\s*\d{3})\b",
            predicate="prerequisite",
            subj_group=1,
            obj_group=2,
            description="Extracts course prerequisite relationships: (CourseA, prerequisite, CourseB)"
        ),
        ExtractionRule(
            rule_id="R02_TAUGHT_BY",
            pattern=r"\b([A-Z]{2,4}\s*\d{3})\b\s*(?:is taught by|is instructed by|taught by)\s*((?:Prof\.|Dr\.|Mr\.|Ms\.)\s+[A-Za-z\.\s]{3,35}|[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
            predicate="taught_by",
            subj_group=1,
            obj_group=2,
            description="Extracts instructor relationships: (Course, taught_by, Instructor)"
        ),
        ExtractionRule(
            rule_id="R03_TEACHES",
            pattern=r"((?:Prof\.|Dr\.|Mr\.|Ms\.)\s+[A-Za-z\.\s]{3,30}|[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*(?:teaches|instructs)\s*(?:the course\s+)?\b([A-Z]{2,4}\s*\d{3})\b",
            predicate="teaches",
            subj_group=1,
            obj_group=2,
            description="Extracts teaching assignments: (Instructor, teaches, Course)"
        ),
        ExtractionRule(
            rule_id="R04_CREDITS",
            pattern=r"\b([A-Z]{2,4}\s*\d{3})\b\s*(?:carries|has|is awarded|worth)\s*(\d+)\s*credits?",
            predicate="credits",
            subj_group=1,
            obj_group=2,
            description="Extracts credit values: (Course, credits, N)"
        ),
        ExtractionRule(
            rule_id="R05_SEMESTER",
            pattern=r"\b([A-Z]{2,4}\s*\d{3})\b\s*(?:is offered in|runs in|scheduled for)\s*(Semester\s*\d+|Fall|Spring)",
            predicate="offered_in",
            subj_group=1,
            obj_group=2,
            description="Extracts semester offerings: (Course, offered_in, Semester)"
        ),
        ExtractionRule(
            rule_id="R06_COURSE_TITLE",
            pattern=r"\b([A-Z]{2,4}\s*\d{3})\b\s*(?:is|named|entitled)\s+(?!offered|taught|belongs|requires|under)([A-Za-z0-9\s]{4,40}?)(?:\.|$)",
            predicate="has_title",
            subj_group=1,
            obj_group=2,
            description="Extracts course title from definitions: (Code, has_title, Title)"
        ),
        ExtractionRule(
            rule_id="R07_DEPT_SCHOOL",
            pattern=r"(?:The\s+)?Department of\s+([A-Za-z\s]{3,30})\s*(?:belongs to|is part of|is under)\s*(?:the\s+)?([A-Za-z\s]{4,30})",
            predicate="belongs_to",
            subj_group=1,
            obj_group=2,
            description="Extracts departmental hierarchy: (Department, belongs_to, School)"
        ),
        ExtractionRule(
            rule_id="R08_COURSE_DEPT",
            pattern=r"\b([A-Z]{2,4}\s*\d{3})\b\s*(?:belongs to the Department of|is offered by the Department of)\s*([A-Za-z\s]{3,30})",
            predicate="department",
            subj_group=1,
            obj_group=2,
            description="Extracts course department: (Course, department, Dept)"
        ),
        ExtractionRule(
            rule_id="R09_ASSESSMENT_WEIGHT",
            pattern=r"(?:In\s+([A-Z]{2,4}\s*\d{3}),?\s+)?([A-Za-z\s]{3,30}?)\s*(?:carries|accounts for|weighs)\s*(\d+)%",
            predicate="assessment_weight",
            subj_group=2,
            obj_group=3,
            description="Extracts assessment percentage: (AssessmentItem, assessment_weight, Percentage)"
        ),
        ExtractionRule(
            rule_id="R10_DEADLINE",
            pattern=r"(?:The\s+)?([A-Za-z0-9\s]{4,35}?)\s*(?:deadline is|is due on|starts on|is scheduled for)\s*([A-Za-z]+\s+\d{1,2}(?:,\s*\d{4})?)",
            predicate="deadline",
            subj_group=1,
            obj_group=2,
            description="Extracts academic deadlines and dates: (Event, deadline, Date)"
        ),
        ExtractionRule(
            rule_id="R11_POLICY_MINIMUM",
            pattern=r"(?:The\s+)?minimum\s+([A-Za-z\s]{3,30}?)\s*(?:requirement is|is|must be)\s*(\d+)%",
            predicate="minimum_requirement",
            subj_group=1,
            obj_group=2,
            description="Extracts minimum percentage requirements: (Policy, minimum_requirement, Value%)"
        ),
        ExtractionRule(
            rule_id="R12_POLICY_THRESHOLD",
            pattern=r"(?:The\s+)?([A-Za-z0-9\s']{3,35}?)\s*(?:threshold is|requires a minimum of|requires at least)\s*([0-9\.]+(?:\s*[A-Za-z%]+)?)",
            predicate="threshold",
            subj_group=1,
            obj_group=2,
            description="Extracts grading or standing thresholds: (Policy/Standing, threshold, Value)"
        ),
        ExtractionRule(
            rule_id="R13_PROGRAMME_CREDITS",
            pattern=r"([A-Za-z\s]{4,45}?(?:Programme|Degree|Artificial Intelligence|Computer Science))\s*(?:requires|needs)\s*(\d+)\s*credits",
            predicate="degree_credits",
            subj_group=1,
            obj_group=2,
            description="Extracts degree completion credit totals: (Programme, degree_credits, Credits)"
        ),
        ExtractionRule(
            rule_id="R14_COURSE_LOAD",
            pattern=r"(?:The\s+)?(maximum|minimum)\s+course load\s*(?:is|must be)\s*(\d+)\s*credits",
            predicate="course_load",
            subj_group=1,
            obj_group=2,
            description="Extracts semester credit load bounds: (maximum/minimum, course_load, Credits)"
        ),
        ExtractionRule(
            rule_id="R15_BRANCH_OF",
            pattern=r"^([A-Z][A-Za-z\s]{2,40}?)\s+is\s+(?:a\s+)?branch of\s+([A-Za-z\s]{3,40})",
            predicate="is_a_branch_of",
            subj_group=1,
            obj_group=2,
            description="Extracts discipline hierarchy: (Discipline, is_a_branch_of, Field)"
        ),
        ExtractionRule(
            rule_id="R16_PART_OF",
            pattern=r"^([A-Z][A-Za-z\s]{2,40}?)\s+is\s+(?:a\s+)?part of\s+([A-Za-z\s]{3,40})",
            predicate="is_part_of",
            subj_group=1,
            obj_group=2,
            description="Extracts compositional hierarchy: (Subfield, is_part_of, Discipline)"
        ),
        ExtractionRule(
            rule_id="R17_HELPS_PURPOSE",
            pattern=r"^([A-Z]{2,4}|[A-Z][A-Za-z\s]{2,30}?)\s+helps\s+([A-Za-z0-9\s]{5,90}?)(?:\.|$)",
            predicate="purpose",
            subj_group=1,
            obj_group=2,
            description="Extracts functional purpose: (Subject, purpose, Description)"
        ),
        ExtractionRule(
            rule_id="R18_AGENT_BEHAVIOR",
            pattern=r"^(?:An?\s+)?([A-Za-z\s]{3,30}?)\s+(observes\s+[A-Za-z\s]+?\s+and\s+takes\s+actions)",
            predicate="behavior",
            subj_group=1,
            obj_group=2,
            description="Extracts agent behavioral definition: (Agent, behavior, Actions)"
        )
    ]


class DocumentExtractor:
    """Extracts structured knowledge triples and unparsed sentences from documents."""
    
    def __init__(self, rules: Optional[List[ExtractionRule]] = None):
        self.rules = rules or get_default_extraction_rules()

    @staticmethod
    def extract_text_from_file(file_path: str) -> str:
        """Reads plain text, markdown, pdf, or docx files."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.txt', '.md']:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        elif ext == '.docx':
            try:
                import docx
                doc = docx.Document(file_path)
                return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            except Exception as e:
                return f"[DOCX Read Error: {e}]"
        elif ext == '.pdf':
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                text = []
                for page in reader.pages:
                    t = page.extract_text()
                    if t:
                        text.append(t)
                return "\n".join(text)
            except Exception as e:
                return f"[PDF Read Error: {e}]"
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()

    def split_into_sentences(self, raw_text: str) -> List[Tuple[int, str]]:
        """Splits text into lines/sentences with line numbers using regex only, preserving abbreviations like Dr. and Prof."""
        lines = raw_text.splitlines()
        sentences: List[Tuple[int, str]] = []
        for line_idx, line in enumerate(lines, start=1):
            line_str = line.strip()
            if not line_str or line_str.startswith("===") or line_str.startswith("---"):
                continue
            # Protect common honorific abbreviations before splitting
            protected = re.sub(r"\b(Dr|Prof|Mr|Ms|Sr|Jr)\.", r"\1_DOT_", line_str, flags=re.IGNORECASE)
            sub_sentences = re.split(r"[.!?]\s+", protected)
            for sub in sub_sentences:
                clean_sub = sub.replace("_DOT_", ".").strip()
                if clean_sub and not clean_sub.startswith("#"):
                    clean_sub = clean_sub.rstrip(".!?:")
                    sentences.append((line_idx, clean_sub))
        return sentences

    def parse_markdown_tables(self, raw_text: str) -> Tuple[List[Triple], List[int]]:
        """Parses structured pipe tables (e.g. Code | Title | Credits | Semester | Prerequisite | Instructor | Department)."""
        triples: List[Triple] = []
        table_lines_indices: List[int] = []
        lines = raw_text.splitlines()

        for idx, line in enumerate(lines, start=1):
            trimmed = line.strip()
            if not trimmed.startswith("|") or not trimmed.endswith("|"):
                continue

            parts = [p.strip() for p in trimmed.split("|")[1:-1]]
            if not parts:
                continue

            # Header or divider
            if "Code" in parts[0] or "code" in parts[0].lower() or all(set(p).issubset({'-', ' ', ':'}) for p in parts if p):
                table_lines_indices.append(idx)
                continue

            # Table row matching: [Code, Title, Credits, Semester, Prerequisite, Instructor, Department]
            table_lines_indices.append(idx)
            if len(parts) >= 6:
                code = parts[0]
                title = parts[1]
                credits_val = parts[2]
                semester = parts[3]
                prereq = parts[4]
                instructor = parts[5]
                dept = parts[6] if len(parts) > 6 else ""

                if code and title:
                    triples.append(Triple(code, "has_title", title, idx, "R_TABLE_TITLE", trimmed))
                if code and credits_val and credits_val.isdigit():
                    triples.append(Triple(code, "credits", credits_val, idx, "R_TABLE_CREDITS", trimmed))
                if code and semester:
                    triples.append(Triple(code, "offered_in", semester, idx, "R_TABLE_SEMESTER", trimmed))
                if code and prereq and prereq.lower() not in ["none", "nil", "-", "n/a"]:
                    for p in re.split(r"[,;]\s*", prereq):
                        if p.strip():
                            triples.append(Triple(code, "prerequisite", p.strip(), idx, "R_TABLE_PREREQ", trimmed))
                if code and instructor and instructor.lower() not in ["tbd", "none", "-"]:
                    triples.append(Triple(code, "taught_by", instructor, idx, "R_TABLE_INSTRUCTOR", trimmed))
                    # Symmetric teaches relation
                    triples.append(Triple(instructor, "teaches", code, idx, "R_TABLE_TEACHES", trimmed))
                if code and dept and dept.lower() not in ["none", "-"]:
                    triples.append(Triple(code, "department", dept, idx, "R_TABLE_DEPT", trimmed))

        return triples, table_lines_indices

    def extract_from_text(self, raw_text: str) -> Dict[str, Any]:
        """Runs rule table and table extraction over raw text."""
        sentences = self.split_into_sentences(raw_text)
        triples_set = set()
        parsed_line_nums = set()
        rule_fire_counts: Dict[str, int] = {}

        # 1. First parse structured tables
        table_triples, table_line_indices = self.parse_markdown_tables(raw_text)
        for t in table_triples:
            triples_set.add(t)
            rule_fire_counts[t.rule_id] = rule_fire_counts.get(t.rule_id, 0) + 1
        parsed_line_nums.update(table_line_indices)

        # 2. Parse prose sentences with rule table
        unparsed_sentences: List[Dict[str, Any]] = []

        for line_idx, sentence in sentences:
            if line_idx in table_line_indices:
                continue

            matched = False
            clean_s = sentence.lstrip("-*• ").strip()

            for rule in self.rules:
                m = rule.pattern.search(clean_s)
                if m:
                    try:
                        # Special handling for assessment with course context
                        if rule.rule_id == "R09_ASSESSMENT_WEIGHT":
                            course_ctx = m.group(1)
                            item = m.group(2).strip()
                            weight = m.group(3).strip()
                            subj = f"{course_ctx} {item}" if course_ctx else item
                            t = Triple(subj, rule.predicate, f"{weight}%", line_idx, rule.rule_id, sentence)
                            triples_set.add(t)
                            # Also store course-specific triple if course is present
                            if course_ctx:
                                t_c = Triple(course_ctx.strip(), "has_assessment", f"{item}: {weight}%", line_idx, rule.rule_id, sentence)
                                triples_set.add(t_c)
                        elif rule.rule_id == "R11_POLICY_MINIMUM":
                            subj = m.group(1).strip()
                            obj = m.group(2).strip()
                            if not obj.endswith("%"):
                                obj = f"{obj}%"
                            t = Triple(subj, rule.predicate, obj, line_idx, rule.rule_id, sentence)
                            triples_set.add(t)
                        else:
                            subj = m.group(rule.subj_group).strip().rstrip(".")
                            obj = m.group(rule.obj_group).strip().rstrip(".")

                            # Clean up leading prefix words
                            subj = re.sub(r"^(The|A|An)\s+", "", subj, flags=re.IGNORECASE)
                            obj = re.sub(r"^(The|A|An)\s+", "", obj, flags=re.IGNORECASE)

                            t = Triple(subj, rule.predicate, obj, line_idx, rule.rule_id, sentence)
                            triples_set.add(t)

                            # If taught_by, also record reciprocal teaches
                            if rule.predicate == "taught_by":
                                t_inv = Triple(obj, "teaches", subj, line_idx, rule.rule_id + "_INV", sentence)
                                triples_set.add(t_inv)

                        matched = True
                        rule_fire_counts[rule.rule_id] = rule_fire_counts.get(rule.rule_id, 0) + 1
                    except Exception:
                        pass

            if matched:
                parsed_line_nums.add(line_idx)
            else:
                unparsed_sentences.append({
                    "line": line_idx,
                    "text": sentence
                })

        triples_list = list(triples_set)
        # Sort triples by source line and subject
        triples_list.sort(key=lambda x: (x.source_line, x.subject, x.predicate))

        return {
            "triples": triples_list,
            "rule_fire_counts": rule_fire_counts,
            "total_sentences": len(sentences) + len(table_line_indices),
            "parsed_sentences_count": len(parsed_line_nums),
            "unparsed_sentences": unparsed_sentences,
            "coverage_percentage": round((len(parsed_line_nums) / max(1, len(parsed_line_nums) + len(unparsed_sentences))) * 100, 2)
        }
