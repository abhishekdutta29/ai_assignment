"""
KnowledgeLens - Web Application Server
Flask-based offline web application implementing all 5 pages and JSON API endpoints.
Course: AID201A - Artificial Intelligence
"""

import os
import json
import csv
import io
from flask import Flask, render_template, request, jsonify, Response, send_file, redirect
from werkzeug.utils import secure_filename

from src.extractor import DocumentExtractor, get_default_extraction_rules
from src.kb import KnowledgeBase
from src.question_parser import QuestionParser
from src.reasoner import ReasoningEngine
from src.answer_generator import AnswerGenerator
from src.evaluator import BenchmarkEvaluator
from src.inference_rules import StudentProfile, get_all_inference_rules

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DATA_DIR = os.path.join(BASE_DIR, "sample_data")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"), static_folder=os.path.join(BASE_DIR, "static"))
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max

# Global in-memory state
kb_instance = KnowledgeBase()
extractor_instance = DocumentExtractor()
student_profile_instance = StudentProfile()
current_document_name = "University Programme Handbook (Built-in Demo)"

def init_default_kb():
    """Initializes Knowledge Base with default University Programme Handbook."""
    global kb_instance, current_document_name
    default_path = os.path.join(SAMPLE_DATA_DIR, "handbook.txt")
    if os.path.exists(default_path):
        text = DocumentExtractor.extract_text_from_file(default_path)
        res = extractor_instance.extract_from_text(text)
        kb_instance.populate(res)
        current_document_name = "University Programme Handbook (Academic Year 2026-2027)"

init_default_kb()

# ------------------------------------------------------------------------------
# PAGE ROUTES
# ------------------------------------------------------------------------------

@app.route("/")
@app.route("/builder")
def page_builder():
    rules = [
        {"id": r.rule_id, "predicate": r.predicate, "desc": r.description}
        for r in get_default_extraction_rules()
    ]
    return render_template(
        "builder.html",
        active_page="builder",
        doc_name=current_document_name,
        rules=rules,
        stats=kb_instance.metadata
    )

@app.route("/explorer")
def page_explorer():
    return redirect("/builder")

@app.route("/qa")
def page_qa():
    return render_template(
        "qa.html",
        active_page="qa",
        profile=student_profile_instance.to_dict(),
        doc_name=current_document_name
    )

@app.route("/eval")
def page_eval():
    return render_template(
        "eval.html",
        active_page="eval",
        doc_name=current_document_name
    )

@app.route("/justification")
def page_justification():
    return redirect("/builder")

# ------------------------------------------------------------------------------
# JSON API ENDPOINTS
# ------------------------------------------------------------------------------

@app.route("/api/kb/suggested-questions", methods=["GET"])
def api_kb_suggested_questions():
    """Generates grounded possible outcome questions derived from current KB triples."""
    triples = kb_instance.triple_store.triples
    courses = [t.subject for t in triples if t.predicate in ["credits", "has_title", "taught_by"]]
    courses = list(dict.fromkeys(courses))  # deduplicate preserving order

    prereq_courses = [t.subject for t in triples if t.predicate == "prerequisite"]
    prereq_courses = list(dict.fromkeys(prereq_courses))

    deadlines = [t.subject for t in triples if t.predicate == "deadline"]
    policies = [t.subject for t in triples if t.predicate in ["minimum_requirement", "threshold"]]

    categories = []

    # 1. Fact Lookup Questions
    fact_qs = []
    # Check concept / definition relations
    branch_triples = [t for t in triples if t.predicate == "is_a_branch_of"]
    part_triples = [t for t in triples if t.predicate == "is_part_of"]
    purpose_triples = [t for t in triples if t.predicate == "purpose"]
    behavior_triples = [t for t in triples if t.predicate == "behavior"]

    if branch_triples:
        fact_qs.append(f"What is {branch_triples[0].subject}?")
    if part_triples:
        fact_qs.append(f"What is {part_triples[0].subject} a part of?")
    if purpose_triples:
        fact_qs.append(f"What does {purpose_triples[0].subject} do?")
    if behavior_triples:
        fact_qs.append(f"What does an {behavior_triples[0].subject} do?")

    if courses:
        c1 = courses[0]
        c2 = courses[min(1, len(courses)-1)]
        fact_qs.append(f"Who teaches {c1}?")
        fact_qs.append(f"How many credits does {c2} carry?")
        fact_qs.append(f"Which semester is {c1} offered in?")
    if prereq_courses:
        fact_qs.append(f"What is the prerequisite for {prereq_courses[0]}?")
    if deadlines:
        fact_qs.append(f"When is the {deadlines[0]} deadline?")
    elif not fact_qs:
        fact_qs.append("What is the minimum attendance requirement?")

    categories = [
        {
            "category": "Factual Lookups",
            "icon": "fa-solid fa-circle-question",
            "tag": "fact",
            "questions": fact_qs[:4]
        }
    ]

    entities = sorted(list(kb_instance.entity_index.canonical_entities))

    return jsonify({
        "status": "success",
        "doc_name": current_document_name,
        "categories": categories,
        "entities": entities
    })


@app.route("/api/kb/summary", methods=["GET"])
def api_kb_summary():
    triples_data = [t.to_dict() for t in kb_instance.triple_store.triples]
    graph_data = kb_instance.graph.to_visjs_graph()
    predicates = kb_instance.triple_store.all_predicates()
    return jsonify({
        "status": "success",
        "doc_name": current_document_name,
        "metadata": kb_instance.metadata,
        "triples": triples_data,
        "graph": graph_data,
        "predicates": predicates,
        "entities": sorted(list(kb_instance.entity_index.canonical_entities)),
        "entity_categories": kb_instance.entity_index.entity_categories,
        "aliases": kb_instance.entity_index.alias_map
    })

@app.route("/api/kb/export", methods=["GET"])
def api_kb_export():
    json_str = kb_instance.to_json()
    return Response(
        json_str,
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment;filename=knowledgelens_kb.json"}
    )

@app.route("/api/kb/load-default", methods=["POST"])
def api_kb_load_default():
    init_default_kb()
    return jsonify({
        "status": "success",
        "message": "Default University Programme Handbook loaded successfully.",
        "stats": kb_instance.metadata,
        "triples_count": kb_instance.triple_store.count()
    })

@app.route("/api/upload", methods=["POST"])
def api_upload():
    global current_document_name, kb_instance
    raw_text = ""
    filename = ""

    if "file" in request.files and request.files["file"].filename != "":
        f = request.files["file"]
        filename = secure_filename(f.filename)
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        f.save(save_path)
        raw_text = DocumentExtractor.extract_text_from_file(save_path)
        current_document_name = filename
    elif "pasted_text" in request.form and request.form["pasted_text"].strip() != "":
        raw_text = request.form["pasted_text"].strip()
        current_document_name = "Custom Pasted Document"
    else:
        return jsonify({"status": "error", "message": "No file uploaded or text provided."}), 400

    if not raw_text:
        return jsonify({"status": "error", "message": "Document content was empty."}), 400

    extraction_res = extractor_instance.extract_from_text(raw_text)
    kb_instance.populate(extraction_res)

    return jsonify({
        "status": "success",
        "message": f"Successfully parsed '{current_document_name}'.",
        "doc_name": current_document_name,
        "triples_count": kb_instance.triple_store.count(),
        "entities_count": len(kb_instance.entity_index.canonical_entities),
        "metadata": kb_instance.metadata
    })

@app.route("/api/ask", methods=["POST"])
def api_ask():
    data = request.get_json() or {}
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"status": "error", "message": "Question is empty."}), 400

    profile_data = data.get("profile")
    if profile_data:
        profile = StudentProfile(
            student_id=profile_data.get("student_id", "STD2026"),
            completed_courses=profile_data.get("completed_courses", []),
            attendance=float(profile_data.get("attendance", 80.0)),
            cgpa=float(profile_data.get("cgpa", 3.8)),
            completed_credits=int(profile_data.get("completed_credits", 90)),
            current_semester_credits=int(profile_data.get("current_semester_credits", 16))
        )
    else:
        profile = student_profile_instance

    parser = QuestionParser(kb_instance.entity_index)
    parsed_q = parser.parse(question, fuzzy=True)

    reasoner = ReasoningEngine(kb_instance)
    reason_res = reasoner.reason(parsed_q, profile=profile, enable_rules=True)

    answer_payload = AnswerGenerator.generate(reason_res, parsed_q)

    return jsonify({
        "status": "success",
        "question": question,
        "parsed_query": parsed_q.to_dict(),
        "answer": answer_payload["answer_text"],
        "answer_status": answer_payload["status"],
        "evidence": answer_payload["evidence"],
        "trace": answer_payload["trace"]
    })

@app.route("/api/profile", methods=["GET", "POST"])
def api_profile():
    global student_profile_instance
    if request.method == "POST":
        data = request.get_json() or {}
        student_profile_instance = StudentProfile(
            student_id=data.get("student_id", "STD2026"),
            completed_courses=data.get("completed_courses", ["CS101", "MAT101", "CS102", "AI201", "AI301", "AI401"]),
            attendance=float(data.get("attendance", 80.0)),
            cgpa=float(data.get("cgpa", 3.8)),
            completed_credits=int(data.get("completed_credits", 92)),
            current_semester_credits=int(data.get("current_semester_credits", 16))
        )
    return jsonify({"status": "success", "profile": student_profile_instance.to_dict()})

@app.route("/api/eval/run", methods=["GET", "POST"])
def api_eval_run():
    test_file = os.path.join(SAMPLE_DATA_DIR, "test_questions.json")
    if not os.path.exists(test_file):
        return jsonify({"status": "error", "message": "Test set not found."}), 404

    with open(test_file, "r", encoding="utf-8") as f:
        questions = json.load(f)

    evaluator = BenchmarkEvaluator(kb_instance)
    report = evaluator.evaluate(questions, run_ablations=True)
    return jsonify({"status": "success", "report": report.to_dict()})

@app.route("/api/eval/export/csv", methods=["GET"])
def api_eval_export_csv():
    test_file = os.path.join(SAMPLE_DATA_DIR, "test_questions.json")
    with open(test_file, "r", encoding="utf-8") as f:
        questions = json.load(f)

    evaluator = BenchmarkEvaluator(kb_instance)
    report = evaluator.evaluate(questions, run_ablations=False)

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["ID", "Question", "Category", "Expected Type", "Actual Type", "Technique", "Result", "Actual Answer", "Latency (ms)"])
    for r in report.question_results:
        cw.writerow([
            r["id"],
            r["question"],
            r["category"],
            r["expected_type"],
            r["actual_type"],
            r["technique"],
            "PASS" if r["passed"] else "FAIL",
            r["actual_answer"],
            r["time_ms"]
        ])

    output = io.BytesIO()
    output.write(si.getvalue().encode("utf-8"))
    output.seek(0)
    return send_file(
        output,
        mimetype="text/csv",
        as_attachment=True,
        download_name="knowledgelens_evaluation.csv"
    )

@app.route("/api/eval/export/json", methods=["GET"])
def api_eval_export_json():
    test_file = os.path.join(SAMPLE_DATA_DIR, "test_questions.json")
    with open(test_file, "r", encoding="utf-8") as f:
        questions = json.load(f)

    evaluator = BenchmarkEvaluator(kb_instance)
    report = evaluator.evaluate(questions, run_ablations=True)

    json_str = json.dumps(report.to_dict(), indent=2)
    return Response(
        json_str,
        mimetype="application/json",
        headers={"Content-Disposition": "attachment;filename=knowledgelens_evaluation.json"}
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
