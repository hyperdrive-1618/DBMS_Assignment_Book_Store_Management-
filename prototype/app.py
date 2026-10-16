"""
Flask Web Application for Training, Programme, and Certificate Management System (TPCMS).
Serves REST API, Interactive UI, Printable Credentials, and MySQL Connector Dashboard.
"""

import os
import json
from flask import Flask, jsonify, request, send_from_directory, render_template

from database.db_manager import DatabaseManager

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config["SECRET_KEY"] = "tpcms-enterprise-secret-key-2026"

# Initialize Database Manager
db_manager = DatabaseManager()

# -----------------------------------------------------------------------------
# Frontend Routes
# -----------------------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/verify/<query>")
def verify_shortcut(query):
    return send_from_directory("static", "index.html")

# -----------------------------------------------------------------------------
# API: Dashboard & Analytics
# -----------------------------------------------------------------------------
@app.route("/api/dashboard", methods=["GET"])
def api_dashboard():
    try:
        metrics = db_manager.get_dashboard_metrics()
        return jsonify({"status": "success", "data": metrics})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# -----------------------------------------------------------------------------
# API: Programmes & Courses
# -----------------------------------------------------------------------------
@app.route("/api/programmes", methods=["GET", "POST"])
def api_programmes():
    if request.method == "POST":
        try:
            data = request.json or {}
            if not data.get("title") or not data.get("category"):
                return jsonify({"status": "error", "message": "Title and Category are required."}), 400
            new_id = db_manager.create_programme(data)
            return jsonify({"status": "success", "programme_id": new_id, "message": "Programme created successfully."}), 201
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    
    category = request.args.get("category")
    status = request.args.get("status")
    search = request.args.get("search")
    programmes = db_manager.get_programmes(category=category, status=status, search=search)
    return jsonify({"status": "success", "data": programmes})

# -----------------------------------------------------------------------------
# API: Trainees
# -----------------------------------------------------------------------------
@app.route("/api/trainees", methods=["GET", "POST"])
def api_trainees():
    if request.method == "POST":
        try:
            data = request.json or {}
            if not data.get("full_name") or not data.get("email"):
                return jsonify({"status": "error", "message": "Full Name and Email are required."}), 400
            new_id = db_manager.create_trainee(data)
            return jsonify({"status": "success", "trainee_id": new_id, "message": "Trainee registered successfully."}), 201
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    
    search = request.args.get("search")
    trainees = db_manager.get_trainees(search=search)
    return jsonify({"status": "success", "data": trainees})

# -----------------------------------------------------------------------------
# API: Enrollments & Progress
# -----------------------------------------------------------------------------
@app.route("/api/enrollments", methods=["GET", "POST"])
def api_enrollments():
    if request.method == "POST":
        try:
            data = request.json or {}
            trainee_id = data.get("trainee_id")
            programme_id = data.get("programme_id")
            if not trainee_id or not programme_id:
                return jsonify({"status": "error", "message": "Trainee ID and Programme ID are required."}), 400
            
            new_id = db_manager.enroll_trainee(int(trainee_id), int(programme_id), data.get("enrollment_date"))
            return jsonify({"status": "success", "enrollment_id": new_id, "message": "Enrollment recorded successfully."}), 201
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    programme_id = request.args.get("programme_id")
    status = request.args.get("status")
    pid = int(programme_id) if programme_id else None
    enrollments = db_manager.get_enrollments(programme_id=pid, status=status)
    return jsonify({"status": "success", "data": enrollments})

@app.route("/api/enrollments/<int:enrollment_id>/progress", methods=["PUT"])
def api_update_progress(enrollment_id):
    try:
        data = request.json or {}
        progress = float(data.get("progress_percentage", 0.0))
        attendance = float(data.get("attendance_percentage", 0.0))
        score = float(data.get("assessment_score")) if data.get("assessment_score") is not None else None
        remarks = data.get("remarks", "")

        db_manager.update_enrollment_progress(enrollment_id, progress, attendance, score, remarks)
        return jsonify({"status": "success", "message": "Progress and performance updated successfully."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# -----------------------------------------------------------------------------
# API: Certificates
# -----------------------------------------------------------------------------
@app.route("/api/certificates", methods=["GET"])
def api_certificates():
    search = request.args.get("search")
    status = request.args.get("status")
    certs = db_manager.get_certificates(search=search, status=status)
    return jsonify({"status": "success", "data": certs})

@app.route("/api/certificates/issue", methods=["POST"])
def api_issue_certificate():
    try:
        data = request.json or {}
        enrollment_id = data.get("enrollment_id")
        if not enrollment_id:
            return jsonify({"status": "error", "message": "Enrollment ID is required."}), 400

        template_style = data.get("template_style", "Classic Royal Navy")
        issued_by = data.get("issued_by", "Academic Board & Certification Authority")

        result = db_manager.issue_certificate(
            int(enrollment_id),
            template_style=template_style,
            issued_by=issued_by
        )
        if result.get("success"):
            return jsonify({"status": "success", "data": result}), 201
        else:
            return jsonify({"status": "error", "message": result.get("message")}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/certificates/verify/<query>", methods=["GET"])
def api_verify_certificate(query):
    cert = db_manager.get_certificate_by_number_or_hash(query.strip())
    if cert:
        return jsonify({"status": "success", "verified": True, "data": cert})
    return jsonify({"status": "not_found", "verified": False, "message": "No authentic certificate matching this credential ID or hash was found."}), 404

# -----------------------------------------------------------------------------
# API: Metadata (Instructors, Departments)
# -----------------------------------------------------------------------------
@app.route("/api/instructors", methods=["GET"])
def api_instructors():
    return jsonify({"status": "success", "data": db_manager.get_instructors()})

@app.route("/api/departments", methods=["GET"])
def api_departments():
    return jsonify({"status": "success", "data": db_manager.get_departments()})

# -----------------------------------------------------------------------------
# API: Database Engine & MySQL Switcher
# -----------------------------------------------------------------------------
@app.route("/api/db/status", methods=["GET"])
def api_db_status():
    status = db_manager.get_database_status()
    return jsonify({"status": "success", "data": status})

@app.route("/api/db/test-mysql", methods=["POST"])
def api_test_mysql():
    config = request.json or {}
    ok, msg = db_manager.test_mysql_connection(config)
    return jsonify({"status": "success" if ok else "error", "connected": ok, "message": msg})

@app.route("/api/db/switch-mysql", methods=["POST"])
def api_switch_mysql():
    config = request.json or {}
    ok, msg = db_manager.switch_to_mysql(config)
    if ok:
        return jsonify({"status": "success", "message": msg})
    return jsonify({"status": "error", "message": msg}), 400

@app.route("/api/db/switch-sqlite", methods=["POST"])
def api_switch_sqlite():
    msg = db_manager.switch_to_sqlite()
    return jsonify({"status": "success", "message": msg})

@app.route("/api/db/execute-sql", methods=["POST"])
def api_execute_sql():
    sql = (request.json or {}).get("sql", "").strip()
    if not sql:
        return jsonify({"status": "error", "message": "Empty SQL statement."}), 400
    try:
        res = db_manager.execute_raw(sql)
        return jsonify({"status": "success", "data": res})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# -----------------------------------------------------------------------------
# Entry Point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5050))
    print(f"🚀 TPCMS Server starting on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
