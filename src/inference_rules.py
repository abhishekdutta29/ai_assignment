"""
KnowledgeLens - Module 2: Symbolic Inference Rules (Horn Clauses)
Classical First-Order Logic IF-THEN rules for forward and backward chaining.
Strictly symbolic; no statistical models or vector similarity.
"""

from typing import List, Dict, Any, Tuple, Optional

class StudentProfile:
    """Represents the factual state of a student for symbolic reasoning."""
    def __init__(self, 
                 student_id: str = "STD2026",
                 completed_courses: Optional[List[str]] = None,
                 attendance: float = 80.0,
                 cgpa: float = 3.8,
                 completed_credits: int = 92,
                 current_semester_credits: int = 16):
        self.student_id = student_id
        self.completed_courses = [c.upper().strip() for c in (completed_courses or ["CS101", "MAT101", "CS102", "AI201", "AI301", "AI401"])]
        self.attendance = attendance
        self.cgpa = cgpa
        self.completed_credits = completed_credits
        self.current_semester_credits = current_semester_credits

    def to_dict(self) -> Dict[str, Any]:
        return {
            "student_id": self.student_id,
            "completed_courses": self.completed_courses,
            "attendance": self.attendance,
            "cgpa": self.cgpa,
            "completed_credits": self.completed_credits,
            "current_semester_credits": self.current_semester_credits
        }


class HornRule:
    """
    Symbolic Horn Clause: Head (consequent) <- Body (antecedents).
    Rule format: IF [condition_1, condition_2, ...] THEN conclusion
    """
    def __init__(self, rule_id: str, name: str, description: str):
        self.rule_id = rule_id
        self.name = name
        self.description = description

    def evaluate(self, profile: StudentProfile, kb_context: Any, target_entity: Optional[str] = None) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Evaluates rule against student profile and KB facts.
        Returns: (fired: bool, explanation: str, supporting_evidence: list)
        """
        raise NotImplementedError


class CourseEligibilityRule(HornRule):
    """IF student has completed ALL prerequisites of course C THEN student is eligible for C."""
    def __init__(self):
        super().__init__(
            rule_id="RULE_COURSE_ELIGIBILITY",
            name="Course Prerequisite Clearance",
            description="IF all prerequisites of course C are completed THEN eligible(Student, C)"
        )

    def evaluate(self, profile: StudentProfile, kb_context: Any, target_course: Optional[str] = None) -> Tuple[bool, str, List[Dict[str, Any]]]:
        if not target_course:
            return False, "No target course specified.", []

        # Find prerequisites of target course from KB triples
        prereq_triples = kb_context.triple_store.find(subject=target_course, predicate="prerequisite")
        prereqs = [t.object for t in prereq_triples]

        evidence = [t.to_dict() for t in prereq_triples]

        if not prereqs:
            return True, f"Course '{target_course}' has no prerequisites. Student is directly eligible to register.", evidence

        missing = [p for p in prereqs if p not in profile.completed_courses]
        if not missing:
            return True, f"Student has completed all required prerequisites ({', '.join(prereqs)}) for '{target_course}'. Rule fires: student is ELIGIBLE.", evidence
        else:
            return False, f"Student is NOT eligible for '{target_course}'. Missing prerequisite(s): {', '.join(missing)}.", evidence


class ExamAttendanceRule(HornRule):
    """IF attendance in course >= 75% THEN eligible for exam ELSE barred from exam."""
    def __init__(self):
        super().__init__(
            rule_id="RULE_EXAM_ATTENDANCE",
            name="Examination Attendance Threshold",
            description="IF attendance >= 75% THEN eligible_for_exam ELSE barred_from_exam"
        )

    def evaluate(self, profile: StudentProfile, kb_context: Any, target_course: Optional[str] = None) -> Tuple[bool, str, List[Dict[str, Any]]]:
        min_att_triples = kb_context.triple_store.find(predicate="minimum_requirement")
        threshold_val = 75.0
        evidence = [t.to_dict() for t in min_att_triples if "attendance" in t.subject.lower()]

        if profile.attendance >= threshold_val:
            return True, f"Student attendance is {profile.attendance}%, meeting the minimum threshold of {threshold_val}%. Rule fires: student is ELIGIBLE for examinations.", evidence
        else:
            return False, f"Student attendance is {profile.attendance}%, falling below the mandatory {threshold_val}% threshold. Rule fires: student is BARRED from examinations.", evidence


class CapstoneEligibilityRule(HornRule):
    """IF completed AI401 AND earned >= 90 credits THEN eligible for Capstone Project AI499."""
    def __init__(self):
        super().__init__(
            rule_id="RULE_CAPSTONE_ELIGIBILITY",
            name="Capstone Project Clearance",
            description="IF completed(AI401) AND credits >= 90 THEN eligible_for_capstone(Student, AI499)"
        )

    def evaluate(self, profile: StudentProfile, kb_context: Any, target_course: Optional[str] = None) -> Tuple[bool, str, List[Dict[str, Any]]]:
        has_ai401 = "AI401" in profile.completed_courses
        has_credits = profile.completed_credits >= 90

        prereq_triples = kb_context.triple_store.find(subject="AI499", predicate="prerequisite")
        evidence = [t.to_dict() for t in prereq_triples]

        if has_ai401 and has_credits:
            return True, f"Student has successfully completed AI401 and acquired {profile.completed_credits} credits (>= 90 required). Rule fires: student is ELIGIBLE for AI499 Capstone Project.", evidence
        
        reasons = []
        if not has_ai401:
            reasons.append("prerequisite AI401 is not yet completed")
        if not has_credits:
            reasons.append(f"accumulated credits ({profile.completed_credits}) is below the required 90 credits")
        return False, f"Student is NOT eligible for AI499 Capstone Project because: {'; '.join(reasons)}.", evidence


class DeansHonourListRule(HornRule):
    """IF CGPA >= 3.75 AND semester credits >= 15 THEN qualifies for Dean's Honour List."""
    def __init__(self):
        super().__init__(
            rule_id="RULE_DEANS_HONOUR_LIST",
            name="Dean's Honour List Qualification",
            description="IF cgpa >= 3.75 AND semester_credits >= 15 THEN qualifies(Student, DeansList)"
        )

    def evaluate(self, profile: StudentProfile, kb_context: Any, target_entity: Optional[str] = None) -> Tuple[bool, str, List[Dict[str, Any]]]:
        threshold_triples = kb_context.triple_store.find(predicate="threshold")
        evidence = [t.to_dict() for t in threshold_triples if "dean" in t.subject.lower()]

        cgpa_ok = profile.cgpa >= 3.75
        credits_ok = profile.current_semester_credits >= 15

        if cgpa_ok and credits_ok:
            return True, f"Student CGPA ({profile.cgpa} >= 3.75) and semester credit load ({profile.current_semester_credits} >= 15) satisfy all criteria. Rule fires: student QUALIFIES for Dean's Honour List.", evidence
        
        failures = []
        if not cgpa_ok:
            failures.append(f"CGPA ({profile.cgpa}) is below 3.75")
        if not credits_ok:
            failures.append(f"semester credits ({profile.current_semester_credits}) is below 15")
        return False, f"Student DOES NOT qualify for Dean's Honour List because: {'; '.join(failures)}.", evidence


class AcademicProbationRule(HornRule):
    """IF CGPA < 2.0 THEN student is placed on Academic Probation."""
    def __init__(self):
        super().__init__(
            rule_id="RULE_ACADEMIC_PROBATION",
            name="Academic Probation Evaluation",
            description="IF cgpa < 2.0 THEN academic_probation(Student)"
        )

    def evaluate(self, profile: StudentProfile, kb_context: Any, target_entity: Optional[str] = None) -> Tuple[bool, str, List[Dict[str, Any]]]:
        evidence = [t.to_dict() for t in kb_context.triple_store.find(predicate="threshold") if "probation" in t.subject.lower()]

        if profile.cgpa < 2.0:
            return True, f"Student CGPA is {profile.cgpa}, falling below the 2.0 minimum standard. Rule fires: student IS on Academic Probation.", evidence
        else:
            return False, f"Student CGPA is {profile.cgpa} (>= 2.0). Rule fires: student is in GOOD STANDING (not on probation).", evidence


def get_all_inference_rules() -> List[HornRule]:
    """Returns the full suite of symbolic Horn inference clauses."""
    return [
        CourseEligibilityRule(),
        ExamAttendanceRule(),
        CapstoneEligibilityRule(),
        DeansHonourListRule(),
        AcademicProbationRule()
    ]
