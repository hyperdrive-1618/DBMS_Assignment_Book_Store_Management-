"""
Database Manager for Training, Programme, and Certificate Management System (TPCMS).
Features:
1. Strict 1NF to 3NF Normalized Architecture.
2. Native MySQL (PyMySQL) Connector with auto-creation of tables, procedures, views, and seeds.
3. Seamless SQLite fallback mode when MySQL is offline so the prototype always runs out-of-the-box.
4. Live credentials reconfiguration & connection test via REST API.
5. SQL Console execution for live DBMS queries.
"""

import os
import sqlite3
import hashlib
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

try:
    import pymysql
    import pymysql.cursors
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False


class DatabaseManager:
    def __init__(self, db_dir: str = None):
        self.db_dir = db_dir or os.path.dirname(os.path.abspath(__file__))
        self.sqlite_path = os.path.join(self.db_dir, "tpcms_local.db")
        
        # Default MySQL connection configurations (can be overridden via ENV or API)
        self.mysql_config = {
            "host": os.getenv("MYSQL_HOST", "localhost"),
            "port": int(os.getenv("MYSQL_PORT", 3306)),
            "user": os.getenv("MYSQL_USER", "root"),
            "password": os.getenv("MYSQL_PASSWORD", ""),
            "database": os.getenv("MYSQL_DB", "training_mgmt_db"),
            "charset": "utf8mb4"
        }
        
        self.active_engine = "sqlite"  # 'mysql' or 'sqlite'
        self.last_error = None
        self.init_database()

    def get_mysql_connection(self, create_db_if_missing: bool = False):
        if not PYMYSQL_AVAILABLE:
            raise RuntimeError("PyMySQL package is not installed.")
        
        cfg = self.mysql_config.copy()
        db_name = cfg.pop("database", "training_mgmt_db")
        
        if create_db_if_missing:
            # Connect without DB to create it if needed
            conn = pymysql.connect(
                host=cfg["host"],
                port=cfg["port"],
                user=cfg["user"],
                password=cfg["password"],
                charset=cfg["charset"],
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=3
            )
            with conn.cursor() as cur:
                cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            conn.commit()
            conn.close()

        # Connect with selected DB
        return pymysql.connect(
            host=cfg["host"],
            port=cfg["port"],
            user=cfg["user"],
            password=cfg["password"],
            database=db_name,
            charset=cfg["charset"],
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=3
        )

    def test_mysql_connection(self, config_override: dict = None) -> Tuple[bool, str]:
        if not PYMYSQL_AVAILABLE:
            return False, "PyMySQL library is not available in the python environment."
        
        test_cfg = self.mysql_config.copy()
        if config_override:
            test_cfg.update(config_override)

        try:
            conn = pymysql.connect(
                host=test_cfg["host"],
                port=int(test_cfg["port"]),
                user=test_cfg["user"],
                password=test_cfg.get("password", ""),
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=4
            )
            with conn.cursor() as cur:
                cur.execute("SELECT VERSION() AS version, USER() AS current_user;")
                info = cur.fetchone()
            conn.close()
            return True, f"Connected to MySQL {info.get('version')} as {info.get('current_user')}"
        except Exception as e:
            return False, str(e)

    def switch_to_mysql(self, config: dict = None) -> Tuple[bool, str]:
        if config:
            self.mysql_config.update(config)
        success, msg = self.test_mysql_connection()
        if success:
            try:
                # Initialize tables on MySQL
                self.setup_mysql_schema()
                self.active_engine = "mysql"
                self.last_error = None
                return True, "Successfully connected and switched to MySQL database!"
            except Exception as e:
                self.last_error = str(e)
                return False, f"Connected to server, but schema creation failed: {e}"
        else:
            self.last_error = msg
            return False, f"Could not connect to MySQL: {msg}"

    def switch_to_sqlite(self):
        self.active_engine = "sqlite"
        self.init_sqlite_schema()
        return True, "Switched to SQLite Local Database mode."

    def init_database(self):
        """Attempts to connect to MySQL; if unavailable, falls back to SQLite seamlessly."""
        can_mysql, msg = self.test_mysql_connection()
        if can_mysql:
            try:
                self.setup_mysql_schema()
                self.active_engine = "mysql"
                print(f"[DB] Connected successfully to MySQL: {msg}")
                return
            except Exception as e:
                print(f"[DB] MySQL init failed ({e}), falling back to SQLite.")
        
        # Fallback to SQLite
        self.active_engine = "sqlite"
        self.init_sqlite_schema()
        print("[DB] Initialized local fallback SQLite database successfully.")

    def init_sqlite_schema(self):
        """Creates the full 1NF-3NF normalized schema and seed data in SQLite."""
        conn = sqlite3.connect(self.sqlite_path)
        cur = conn.cursor()
        
        # Enable Foreign Keys in SQLite
        cur.execute("PRAGMA foreign_keys = ON;")
        
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS departments (
            department_id INTEGER PRIMARY KEY AUTOINCREMENT,
            dept_code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            head_of_dept TEXT,
            budget REAL DEFAULT 0.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS instructors (
            instructor_id INTEGER PRIMARY KEY AUTOINCREMENT,
            instructor_code TEXT NOT NULL UNIQUE,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT,
            specialization TEXT NOT NULL,
            qualification TEXT,
            experience_years INTEGER DEFAULT 3,
            bio TEXT,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS programmes (
            programme_id INTEGER PRIMARY KEY AUTOINCREMENT,
            programme_code TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            level TEXT DEFAULT 'Intermediate',
            duration_hours INTEGER NOT NULL DEFAULT 40,
            max_seats INTEGER NOT NULL DEFAULT 30,
            description TEXT,
            syllabus_summary TEXT,
            instructor_id INTEGER,
            min_passing_score REAL DEFAULT 75.00,
            min_attendance_pct REAL DEFAULT 80.00,
            status TEXT DEFAULT 'Open for Enrollment',
            fee REAL DEFAULT 0.00,
            start_date TEXT,
            end_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (instructor_id) REFERENCES instructors(instructor_id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS trainees (
            trainee_id INTEGER PRIMARY KEY AUTOINCREMENT,
            trainee_code TEXT NOT NULL UNIQUE,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT,
            organization TEXT DEFAULT 'Corporate Division',
            designation TEXT DEFAULT 'Associate',
            department_id INTEGER,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS enrollments (
            enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            trainee_id INTEGER NOT NULL,
            programme_id INTEGER NOT NULL,
            enrollment_date TEXT NOT NULL,
            status TEXT DEFAULT 'Enrolled',
            progress_percentage REAL DEFAULT 0.00,
            attendance_percentage REAL DEFAULT 0.00,
            assessment_score REAL,
            completion_date TEXT,
            remarks TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (trainee_id) REFERENCES trainees(trainee_id) ON DELETE CASCADE,
            FOREIGN KEY (programme_id) REFERENCES programmes(programme_id) ON DELETE CASCADE,
            UNIQUE(trainee_id, programme_id)
        );

        CREATE TABLE IF NOT EXISTS certificates (
            certificate_id INTEGER PRIMARY KEY AUTOINCREMENT,
            certificate_number TEXT NOT NULL UNIQUE,
            enrollment_id INTEGER NOT NULL UNIQUE,
            issue_date TEXT NOT NULL,
            expiry_date TEXT,
            grade TEXT DEFAULT 'Certified',
            verification_hash TEXT NOT NULL UNIQUE,
            template_style TEXT DEFAULT 'Classic Royal Navy',
            status TEXT DEFAULT 'Active',
            issued_by TEXT DEFAULT 'Academic Board & Certification Authority',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id INTEGER,
            details TEXT,
            performed_by TEXT DEFAULT 'System Admin',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Check if seed data exists
        cur.execute("SELECT COUNT(*) FROM departments;")
        if cur.fetchone()[0] == 0:
            self._seed_sqlite_data(cur)
            
        conn.commit()
        conn.close()

    def _seed_sqlite_data(self, cur):
        # Insert Departments
        cur.executemany("""
        INSERT INTO departments (dept_code, name, head_of_dept, budget) VALUES (?, ?, ?, ?);
        """, [
            ('DEPT-IT', 'Information Technology & Engineering', 'Dr. Marcus Vance', 150000.00),
            ('DEPT-AI', 'Artificial Intelligence & Data Labs', 'Dr. Elena Rostova', 220000.00),
            ('DEPT-SEC', 'Cybersecurity Operations & Defense', 'Commander Alan Sterling', 180000.00),
            ('DEPT-MGMT', 'Executive Leadership & Strategy', 'Sophia Chen, MBA', 95000.00),
            ('DEPT-FIN', 'FinTech & Blockchain Research', 'Julian Thorne', 120000.00)
        ])

        # Insert Instructors
        cur.executemany("""
        INSERT INTO instructors (instructor_code, full_name, email, phone, specialization, qualification, experience_years, bio) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, [
            ('INST-001', 'Prof. Alexander Wright', 'a.wright@academy.org', '+1 555-0192', 'Full-Stack Cloud & Microservices', 'Ph.D. in Computer Science (MIT)', 12, 'Former Principal Architect at AWS; specialist in distributed cloud systems and Kubernetes.'),
            ('INST-002', 'Dr. Maya Lin', 'm.lin@academy.org', '+1 555-0144', 'Machine Learning & Generative AI', 'Ph.D. in AI (Stanford)', 9, 'Senior AI Research Fellow published in NeurIPS, specializing in LLM alignment and neural networks.'),
            ('INST-003', 'Nathaniel Drake', 'n.drake@academy.org', '+1 555-0188', 'Offensive & Defensive Cybersecurity', 'CISSP, OSCP, CEH Master', 14, 'Veteran Red Team Lead with military-grade threat assessment and zero-day defense experience.'),
            ('INST-004', 'Sarah Jenkins', 's.jenkins@academy.org', '+1 555-0123', 'Agile Product Management & DevOps', 'PMP, Scrum Master Fellow', 10, 'Enterprise Transformation Coach who advised Fortune 500 tech teams across Silicon Valley.')
        ])

        # Insert Programmes
        cur.executemany("""
        INSERT INTO programmes (programme_code, title, category, level, duration_hours, max_seats, description, syllabus_summary, instructor_id, min_passing_score, min_attendance_pct, status, fee, start_date, end_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, [
            ('PROG-AI-801', 'Applied Generative AI & Large Language Models', 'Artificial Intelligence', 'Advanced', 60, 25, 'Master transformer architectures, fine-tuning, retrieval-augmented generation (RAG), and agentic workflows with hands-on deployments.', '1. Transformers & Attention\n2. Prompt Engineering & Vector DBs\n3. RAG Architecture\n4. Agentic AI & Tool Integration\n5. Production Optimization', 2, 80.00, 85.00, 'In Progress', 1250.00, '2026-08-01', '2026-10-15'),
            ('PROG-CLOUD-402', 'Enterprise Cloud Architect & Kubernetes Masterclass', 'Cloud Computing', 'Intermediate', 48, 30, 'Deep dive into hybrid cloud architectures, container orchestration, microservices resilient networking, and CI/CD pipelines.', '1. Cloud Infrastructure as Code\n2. Kubernetes Pods, Ingress & Mesh\n3. Observability with Prometheus\n4. Cloud Security & FinOps', 1, 75.00, 80.00, 'Open for Enrollment', 980.00, '2026-10-15', '2026-11-30'),
            ('PROG-CYBER-905', 'Zero Trust Architecture & Threat Intelligence Defense', 'Cybersecurity', 'Advanced', 54, 20, 'Hands-on offensive penetration testing, incident response, packet forensics, and Zero Trust implementation frameworks.', '1. Threat Modeling\n2. Network Forensics\n3. Zero Trust Identity & Access\n4. Red/Blue Simulation Labs\n5. Regulatory Compliance', 3, 85.00, 90.00, 'In Progress', 1450.00, '2026-07-10', '2026-09-28'),
            ('PROG-DEV-204', 'Modern Full-Stack Engineering with React & Node', 'Software Engineering', 'Beginner', 40, 35, 'Comprehensive fundamentals to modern reactive frontends, REST & GraphQL APIs, database optimization, and secure session management.', '1. Modern JavaScript & React\n2. Backend REST APIs with Node\n3. Relational Schema & ORMs\n4. Authentication & Deployment', 1, 75.00, 80.00, 'Completed', 750.00, '2026-05-01', '2026-06-20'),
            ('PROG-MGMT-601', 'Strategic Agile Leadership & Executive Coaching', 'Management', 'Executive', 32, 18, 'Designed for engineering leads and VP-level executives to drive high-velocity software cultures and strategic change management.', '1. Servant Leadership\n2. Value Stream Mapping\n3. OKRs & Metric Systems\n4. High-Performance Team Dynamics', 4, 80.00, 85.00, 'Open for Enrollment', 1600.00, '2026-11-01', '2026-12-10')
        ])

        # Insert Trainees
        cur.executemany("""
        INSERT INTO trainees (trainee_code, full_name, email, phone, organization, designation, department_id, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, [
            ('TRN-1001', 'Elena Rostova', 'elena.rostova@techcorp.io', '+1 555-3291', 'Apex Tech Solutions', 'Lead Data Scientist', 2, 'Active'),
            ('TRN-1002', 'Liam O''Connor', 'liam.oconnor@skyward.org', '+1 555-4421', 'Skyward Networks', 'Senior DevOps Engineer', 1, 'Active'),
            ('TRN-1003', 'Priya Sharma', 'priya.sharma@cyberdefense.in', '+1 555-8812', 'Vanguard Security Labs', 'Security Operations Analyst', 3, 'Active'),
            ('TRN-1004', 'Carlos Mendez', 'carlos.m@globalfin.com', '+1 555-9019', 'Global Horizon Capital', 'Principal Software Engineer', 1, 'Active'),
            ('TRN-1005', 'Amina Al-Mansoor', 'amina.m@innovate.ae', '+1 555-6672', 'Emirates Innovation Hub', 'Product Strategy Director', 4, 'Active'),
            ('TRN-1006', 'Dmitri Volkov', 'dmitri.v@datacore.net', '+1 555-7733', 'DataCore Systems', 'ML Infrastructure Engineer', 2, 'Active'),
            ('TRN-1007', 'Kavita Patel', 'kavita.patel@horizon.edu', '+1 555-1129', 'Apex Tech Solutions', 'Junior Full-Stack Dev', 1, 'Active')
        ])

        # Insert Enrollments
        cur.executemany("""
        INSERT INTO enrollments (trainee_id, programme_id, enrollment_date, status, progress_percentage, attendance_percentage, assessment_score, completion_date, remarks)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, [
            (1, 1, '2026-08-01', 'Completed', 100.00, 96.00, 94.50, '2026-10-02', 'Exemplary capstone project on multi-agent RAG pipeline.'),
            (2, 2, '2026-08-10', 'In Progress', 78.00, 88.00, 84.00, None, 'Strong progress in Kubernetes lab sessions.'),
            (3, 3, '2026-07-10', 'Completed', 100.00, 95.00, 96.00, '2026-09-25', 'Top scorer in Red/Blue defensive simulation drill.'),
            (4, 4, '2026-05-01', 'Completed', 100.00, 90.00, 89.00, '2026-06-20', 'Successfully delivered responsive web platform.'),
            (5, 5, '2026-09-01', 'In Progress', 45.00, 92.00, 88.00, None, 'Active participation in executive case studies.'),
            (6, 1, '2026-08-01', 'In Progress', 82.00, 85.00, 78.50, None, 'Undergoing final neural model fine-tuning benchmark.'),
            (7, 4, '2026-05-01', 'Completed', 100.00, 92.00, 91.00, '2026-06-20', 'Outstanding frontend architecture submission.')
        ])

        # Insert Certificates (Strict 3NF: References enrollment_id only)
        cur.executemany("""
        INSERT INTO certificates (certificate_number, enrollment_id, issue_date, expiry_date, grade, verification_hash, template_style, status, issued_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, [
            ('CERT-2026-89101', 1, '2026-10-02', '2028-10-02', 'Honors', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'Classic Royal Navy', 'Active', 'Dr. Maya Lin & Board of Examiners'),
            ('CERT-2026-44219', 3, '2026-09-25', '2028-09-25', 'Distinction', 'ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb', 'Obsidian Gold Seal', 'Active', 'Nathaniel Drake & Defense Directorate'),
            ('CERT-2026-30114', 4, '2026-06-20', '2028-06-20', 'Honors', '4e07408562bedb8b60ce05c1decfe3ad16b72230967de01f640b7e4729b49fce', 'Modern Emerald Elegance', 'Active', 'Prof. Alexander Wright & Tech Board'),
            ('CERT-2026-77823', 7, '2026-06-20', '2028-06-20', 'Distinction', '4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a', 'Modern Emerald Elegance', 'Active', 'Prof. Alexander Wright & Tech Board')
        ])

        # Insert Audit Logs
        cur.executemany("""
        INSERT INTO audit_logs (action, entity_type, entity_id, details, performed_by) VALUES (?, ?, ?, ?, ?);
        """, [
            ('SYSTEM_INIT', 'DATABASE', 1, 'Initial database schema and seeds generated successfully.', 'Root Administrator'),
            ('CERTIFICATE_ISSUED', 'CERTIFICATE', 1, 'Issued CERT-2026-89101 to enrollment 1 with Honors.', 'Academic Board'),
            ('CERTIFICATE_ISSUED', 'CERTIFICATE', 2, 'Issued CERT-2026-44219 to enrollment 3 with Distinction.', 'Defense Directorate'),
            ('CERTIFICATE_ISSUED', 'CERTIFICATE', 3, 'Issued CERT-2026-30114 to enrollment 4 with Honors.', 'Tech Board'),
            ('CERTIFICATE_ISSUED', 'CERTIFICATE', 4, 'Issued CERT-2026-77823 to enrollment 7 with Distinction.', 'Tech Board')
        ])

    def setup_mysql_schema(self):
        """Executes database/schema.sql onto the target MySQL database."""
        schema_path = os.path.join(self.db_dir, "schema.sql")
        if not os.path.exists(schema_path):
            raise FileNotFoundError(f"Schema file not found at {schema_path}")

        # Ensure database exists first
        self.get_mysql_connection(create_db_if_missing=True)
        
        conn = self.get_mysql_connection()
        with open(schema_path, "r", encoding="utf-8") as f:
            sql_script = f.read()

        # Split statements, handling DELIMITER block for stored procedures
        statements = []
        delimiter = ";"
        current_stmt = []

        for line in sql_script.splitlines():
            line_strip = line.strip()
            if line_strip.upper().startswith("DELIMITER"):
                parts = line_strip.split()
                if len(parts) >= 2:
                    delimiter = parts[1]
                continue
            
            if delimiter != ";" and delimiter in line_strip:
                stmt_part = line.replace(delimiter, ";")
                current_stmt.append(stmt_part)
                statements.append("\n".join(current_stmt))
                current_stmt = []
            elif delimiter == ";" and line_strip.endswith(";"):
                current_stmt.append(line)
                statements.append("\n".join(current_stmt))
                current_stmt = []
            else:
                if line_strip and not line_strip.startswith("--") and not line_strip.startswith("/*") and not line_strip.startswith("*"):
                    current_stmt.append(line)

        with conn.cursor() as cur:
            cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
            for stmt in statements:
                stmt = stmt.strip()
                if stmt:
                    try:
                        cur.execute(stmt)
                    except Exception as err:
                        print(f"[MySQL Setup Warning] {err} on stmt: {stmt[:60]}")
            cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
        conn.commit()
        conn.close()

    def query(self, sql: str, params: tuple = None, fetch_all: bool = True) -> Any:
        """Executes a query and returns dict results in both MySQL and SQLite."""
        params = params or ()
        if self.active_engine == "mysql":
            conn = self.get_mysql_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    if sql.strip().upper().startswith(("SELECT", "SHOW", "DESCRIBE", "EXPLAIN")):
                        return cur.fetchall() if fetch_all else cur.fetchone()
                    else:
                        conn.commit()
                        return cur.lastrowid
            finally:
                conn.close()
        else:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            try:
                cur = conn.cursor()
                sqlite_sql = sql.replace("%s", "?")
                cur.execute(sqlite_sql, params)
                if sql.strip().upper().startswith(("SELECT", "SHOW", "DESCRIBE", "PRAGMA")):
                    rows = cur.fetchall() if fetch_all else cur.fetchone()
                    if rows is None:
                        return None
                    if fetch_all:
                        return [dict(r) for r in rows]
                    else:
                        return dict(rows)
                else:
                    conn.commit()
                    return cur.lastrowid
            finally:
                conn.close()

    def execute_raw(self, sql: str) -> Dict[str, Any]:
        """Utility for DBMS assignment query console tester."""
        if self.active_engine == "mysql":
            conn = self.get_mysql_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    if cur.description:
                        columns = [desc[0] for desc in cur.description]
                        rows = cur.fetchall()
                        return {"columns": columns, "rows": rows, "count": len(rows), "engine": "mysql"}
                    conn.commit()
                    return {"affected_rows": cur.rowcount, "engine": "mysql"}
            finally:
                conn.close()
        else:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            try:
                cur = conn.cursor()
                cur.execute(sql)
                if cur.description:
                    columns = [desc[0] for desc in cur.description]
                    rows = [dict(r) for r in cur.fetchall()]
                    return {"columns": columns, "rows": rows, "count": len(rows), "engine": "sqlite"}
                conn.commit()
                return {"affected_rows": cur.rowcount, "engine": "sqlite"}
            finally:
                conn.close()

    # ------------------ High Level Application Methods ------------------

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        trainees_cnt = self.query("SELECT COUNT(*) AS cnt FROM trainees;", fetch_all=False)["cnt"]
        programmes_cnt = self.query("SELECT COUNT(*) AS cnt FROM programmes;", fetch_all=False)["cnt"]
        active_prog_cnt = self.query("SELECT COUNT(*) AS cnt FROM programmes WHERE status != 'Completed' AND status != 'Archived';", fetch_all=False)["cnt"]
        certs_cnt = self.query("SELECT COUNT(*) AS cnt FROM certificates WHERE status = 'Active';", fetch_all=False)["cnt"]
        enrollments_cnt = self.query("SELECT COUNT(*) AS cnt FROM enrollments;", fetch_all=False)["cnt"]
        completed_cnt = self.query("SELECT COUNT(*) AS cnt FROM enrollments WHERE status = 'Completed';", fetch_all=False)["cnt"]
        
        avg_score_res = self.query("SELECT ROUND(AVG(assessment_score), 1) AS avg_s FROM enrollments WHERE assessment_score IS NOT NULL;", fetch_all=False)
        avg_score = avg_score_res["avg_s"] if avg_score_res and avg_score_res["avg_s"] is not None else 85.0

        completion_rate = round((completed_cnt / enrollments_cnt * 100), 1) if enrollments_cnt > 0 else 0.0

        # Program category distribution
        cat_distribution = self.query("""
            SELECT category, COUNT(*) as count 
            FROM programmes 
            GROUP BY category 
            ORDER BY count DESC;
        """)

        # Recent certificates (retrieved with 3NF JOIN through enrollments)
        recent_certs = self.query("""
            SELECT c.certificate_number, c.issue_date, c.grade, e.assessment_score AS score,
                   t.full_name AS trainee_name, p.title AS programme_title
            FROM certificates c
            JOIN enrollments e ON c.enrollment_id = e.enrollment_id
            JOIN trainees t ON e.trainee_id = t.trainee_id
            JOIN programmes p ON e.programme_id = p.programme_id
            ORDER BY c.certificate_id DESC
            LIMIT 5;
        """)

        # Recent Activity / Audit
        recent_logs = self.query("""
            SELECT action, entity_type, details, performed_by, timestamp
            FROM audit_logs
            ORDER BY log_id DESC
            LIMIT 6;
        """)

        return {
            "total_trainees": trainees_cnt,
            "total_programmes": programmes_cnt,
            "active_programmes": active_prog_cnt,
            "total_certificates": certs_cnt,
            "total_enrollments": enrollments_cnt,
            "completion_rate": completion_rate,
            "avg_assessment_score": avg_score,
            "categories": cat_distribution,
            "recent_certificates": recent_certs,
            "recent_logs": recent_logs,
            "engine": self.active_engine,
            "mysql_host": self.mysql_config["host"],
            "mysql_db": self.mysql_config["database"]
        }

    def get_programmes(self, category: str = None, status: str = None, search: str = None) -> List[Dict[str, Any]]:
        sql = """
            SELECT p.*, i.full_name AS instructor_name, i.email AS instructor_email,
                   (SELECT COUNT(*) FROM enrollments e WHERE e.programme_id = p.programme_id) AS enrolled_count,
                   (SELECT COUNT(*) FROM certificates c 
                    JOIN enrollments e ON c.enrollment_id = e.enrollment_id 
                    WHERE e.programme_id = p.programme_id) AS certs_issued
            FROM programmes p
            LEFT JOIN instructors i ON p.instructor_id = i.instructor_id
            WHERE 1=1
        """
        params = []
        if category and category != "All":
            sql += " AND p.category = %s"
            params.append(category)
        if status and status != "All":
            sql += " AND p.status = %s"
            params.append(status)
        if search:
            sql += " AND (p.title LIKE %s OR p.programme_code LIKE %s OR p.description LIKE %s)"
            pattern = f"%{search}%"
            params.extend([pattern, pattern, pattern])
        
        sql += " ORDER BY p.programme_id DESC;"
        return self.query(sql, tuple(params))

    def create_programme(self, data: dict) -> int:
        code = data.get("programme_code") or f"PROG-GEN-{int(datetime.now().timestamp()) % 10000}"
        sql = """
            INSERT INTO programmes 
            (programme_code, title, category, level, duration_hours, max_seats, description, syllabus_summary, instructor_id, min_passing_score, min_attendance_pct, status, fee, start_date, end_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        new_id = self.query(sql, (
            code,
            data.get("title"),
            data.get("category", "Technology"),
            data.get("level", "Intermediate"),
            int(data.get("duration_hours", 40)),
            int(data.get("max_seats", 30)),
            data.get("description", ""),
            data.get("syllabus_summary", ""),
            data.get("instructor_id") or None,
            float(data.get("min_passing_score", 75.0)),
            float(data.get("min_attendance_pct", 80.0)),
            data.get("status", "Open for Enrollment"),
            float(data.get("fee", 0.0)),
            data.get("start_date") or None,
            data.get("end_date") or None
        ))
        self.log_audit("CREATE_PROGRAMME", "PROGRAMME", new_id, f"Created programme {code}: {data.get('title')}")
        return new_id

    def get_trainees(self, search: str = None) -> List[Dict[str, Any]]:
        sql = """
            SELECT t.*, d.name AS department_name, d.dept_code,
                   (SELECT COUNT(*) FROM enrollments e WHERE e.trainee_id = t.trainee_id) AS total_courses,
                   (SELECT COUNT(*) FROM certificates c 
                    JOIN enrollments e ON c.enrollment_id = e.enrollment_id 
                    WHERE e.trainee_id = t.trainee_id) AS total_certificates
            FROM trainees t
            LEFT JOIN departments d ON t.department_id = d.department_id
            WHERE 1=1
        """
        params = []
        if search:
            sql += " AND (t.full_name LIKE %s OR t.email LIKE %s OR t.trainee_code LIKE %s OR t.organization LIKE %s)"
            pat = f"%{search}%"
            params.extend([pat, pat, pat, pat])
        
        sql += " ORDER BY t.trainee_id DESC;"
        return self.query(sql, tuple(params))

    def create_trainee(self, data: dict) -> int:
        code = data.get("trainee_code") or f"TRN-{int(datetime.now().timestamp()) % 10000}"
        sql = """
            INSERT INTO trainees (trainee_code, full_name, email, phone, organization, designation, department_id, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """
        new_id = self.query(sql, (
            code,
            data.get("full_name"),
            data.get("email"),
            data.get("phone", ""),
            data.get("organization", "Corporate Division"),
            data.get("designation", "Staff"),
            data.get("department_id") or None,
            data.get("status", "Active")
        ))
        self.log_audit("CREATE_TRAINEE", "TRAINEE", new_id, f"Registered trainee {code} ({data.get('full_name')})")
        return new_id

    def get_enrollments(self, programme_id: int = None, status: str = None) -> List[Dict[str, Any]]:
        sql = """
            SELECT e.*, t.full_name AS trainee_name, t.email AS trainee_email, t.trainee_code, t.organization,
                   p.title AS programme_title, p.programme_code, p.min_passing_score, p.min_attendance_pct,
                   c.certificate_number, c.certificate_id, c.verification_hash
            FROM enrollments e
            JOIN trainees t ON e.trainee_id = t.trainee_id
            JOIN programmes p ON e.programme_id = p.programme_id
            LEFT JOIN certificates c ON e.enrollment_id = c.enrollment_id
            WHERE 1=1
        """
        params = []
        if programme_id:
            sql += " AND e.programme_id = %s"
            params.append(programme_id)
        if status and status != "All":
            sql += " AND e.status = %s"
            params.append(status)
        sql += " ORDER BY e.enrollment_id DESC;"
        return self.query(sql, tuple(params))

    def enroll_trainee(self, trainee_id: int, programme_id: int, enrollment_date: str = None) -> int:
        edate = enrollment_date or datetime.now().strftime("%Y-%m-%d")
        sql = """
            INSERT INTO enrollments (trainee_id, programme_id, enrollment_date, status, progress_percentage, attendance_percentage)
            VALUES (%s, %s, %s, 'Enrolled', 0.00, 0.00);
        """
        new_id = self.query(sql, (trainee_id, programme_id, edate))
        self.log_audit("ENROLL_TRAINEE", "ENROLLMENT", new_id, f"Enrolled trainee {trainee_id} into programme {programme_id}")
        return new_id

    def update_enrollment_progress(self, enrollment_id: int, progress: float, attendance: float, score: Optional[float], remarks: str = "") -> None:
        status = "In Progress"
        comp_date = None
        if progress >= 100.0:
            status = "Completed"
            comp_date = datetime.now().strftime("%Y-%m-%d")

        sql = """
            UPDATE enrollments
            SET progress_percentage = %s, attendance_percentage = %s, assessment_score = %s, 
                status = %s, completion_date = %s, remarks = %s
            WHERE enrollment_id = %s;
        """
        self.query(sql, (progress, attendance, score, status, comp_date, remarks, enrollment_id))
        self.log_audit("UPDATE_PROGRESS", "ENROLLMENT", enrollment_id, f"Updated progress: {progress}%, score: {score}")

    def get_certificates(self, search: str = None, status: str = None) -> List[Dict[str, Any]]:
        # 3NF Query joining through enrollments
        sql = """
            SELECT c.*, e.assessment_score AS score, e.attendance_percentage,
                   t.trainee_id, t.full_name AS trainee_name, t.email AS trainee_email, t.trainee_code, t.organization,
                   p.programme_id, p.title AS programme_title, p.programme_code, p.duration_hours, p.category AS programme_category,
                   i.full_name AS instructor_name
            FROM certificates c
            JOIN enrollments e ON c.enrollment_id = e.enrollment_id
            JOIN trainees t ON e.trainee_id = t.trainee_id
            JOIN programmes p ON e.programme_id = p.programme_id
            LEFT JOIN instructors i ON p.instructor_id = i.instructor_id
            WHERE 1=1
        """
        params = []
        if status and status != "All":
            sql += " AND c.status = %s"
            params.append(status)
        if search:
            sql += " AND (c.certificate_number LIKE %s OR t.full_name LIKE %s OR p.title LIKE %s OR c.verification_hash LIKE %s)"
            pat = f"%{search}%"
            params.extend([pat, pat, pat, pat])
        sql += " ORDER BY c.certificate_id DESC;"
        return self.query(sql, tuple(params))

    def get_certificate_by_number_or_hash(self, query: str) -> Optional[Dict[str, Any]]:
        # 3NF Query joining through enrollments
        sql = """
            SELECT c.*, e.assessment_score AS score, e.attendance_percentage,
                   t.trainee_id, t.full_name AS trainee_name, t.email AS trainee_email, t.trainee_code, t.organization, t.designation,
                   p.programme_id, p.title AS programme_title, p.programme_code, p.duration_hours, p.category, p.level,
                   i.full_name AS instructor_name, i.qualification AS instructor_qualification
            FROM certificates c
            JOIN enrollments e ON c.enrollment_id = e.enrollment_id
            JOIN trainees t ON e.trainee_id = t.trainee_id
            JOIN programmes p ON e.programme_id = p.programme_id
            LEFT JOIN instructors i ON p.instructor_id = i.instructor_id
            WHERE c.certificate_number = %s OR c.verification_hash = %s;
        """
        return self.query(sql, (query, query), fetch_all=False)

    def issue_certificate(self, enrollment_id: int, template_style: str = "Classic Royal Navy", issued_by: str = "Board of Certification") -> Dict[str, Any]:
        # Validate eligibility
        enrollment = self.query("""
            SELECT e.*, p.min_passing_score, p.min_attendance_pct, p.programme_code, p.title as prog_title,
                   t.full_name as trainee_name
            FROM enrollments e
            JOIN programmes p ON e.programme_id = p.programme_id
            JOIN trainees t ON e.trainee_id = t.trainee_id
            WHERE e.enrollment_id = %s;
        """, (enrollment_id,), fetch_all=False)

        if not enrollment:
            return {"success": False, "message": "Enrollment record not found."}

        # Check if already issued
        existing = self.query("SELECT certificate_number FROM certificates WHERE enrollment_id = %s;", (enrollment_id,), fetch_all=False)
        if existing:
            return {"success": False, "message": f"Certificate already issued ({existing['certificate_number']})."}

        score = enrollment["assessment_score"] or 0.0
        attendance = enrollment["attendance_percentage"] or 0.0
        min_score = enrollment["min_passing_score"] or 75.0
        min_att = enrollment["min_attendance_pct"] or 80.0

        if score < min_score:
            return {"success": False, "message": f"Assessment score ({score}%) is below minimum passing requirement ({min_score}%)."}
        if attendance < min_att:
            return {"success": False, "message": f"Attendance ({attendance}%) is below minimum required attendance ({min_att}%)."}

        # Determine grade honors
        if score >= 95.0:
            grade = "Distinction"
        elif score >= 88.0:
            grade = "Honors"
        elif score >= 80.0:
            grade = "Certified"
        else:
            grade = "Pass"

        # Generate unique certificate number
        year = datetime.now().year
        rand_suffix = (int(datetime.now().timestamp() * 1000) % 90000) + 10000
        cert_number = f"CERT-{year}-{rand_suffix}"

        # Cryptographic Verification Hash
        raw_token = f"{cert_number}-{enrollment['trainee_id']}-{enrollment['programme_id']}-{datetime.now().isoformat()}"
        verification_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        issue_date = datetime.now().strftime("%Y-%m-%d")
        expiry_date = f"{year + 2}-{datetime.now().strftime('%m-%d')}"

        # Insert Certificate (Strict 3NF referencing enrollment_id)
        sql = """
            INSERT INTO certificates 
            (certificate_number, enrollment_id, issue_date, expiry_date, grade, verification_hash, template_style, status, issued_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Active', %s);
        """
        cert_id = self.query(sql, (
            cert_number,
            enrollment_id,
            issue_date,
            expiry_date,
            grade,
            verification_hash,
            template_style,
            issued_by
        ))

        # Mark enrollment completed
        self.query("""
            UPDATE enrollments 
            SET status = 'Completed', completion_date = %s, progress_percentage = 100.00
            WHERE enrollment_id = %s;
        """, (issue_date, enrollment_id))

        self.log_audit("ISSUE_CERTIFICATE", "CERTIFICATE", cert_id, f"Granted {cert_number} ({grade}) to {enrollment['trainee_name']}")

        return {
            "success": True,
            "certificate_id": cert_id,
            "certificate_number": cert_number,
            "verification_hash": verification_hash,
            "grade": grade,
            "score": score,
            "recipient": enrollment["trainee_name"],
            "programme": enrollment["prog_title"]
        }

    def get_instructors(self) -> List[Dict[str, Any]]:
        return self.query("SELECT * FROM instructors ORDER BY full_name ASC;")

    def get_departments(self) -> List[Dict[str, Any]]:
        return self.query("SELECT * FROM departments ORDER BY name ASC;")

    def log_audit(self, action: str, entity_type: str, entity_id: Optional[int], details: str, performed_by: str = "System Admin"):
        sql = """
            INSERT INTO audit_logs (action, entity_type, entity_id, details, performed_by, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        self.query(sql, (action, entity_type, entity_id, details, performed_by, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    def get_database_status(self) -> Dict[str, Any]:
        can_mysql, mysql_info = self.test_mysql_connection()
        return {
            "active_engine": self.active_engine,
            "mysql_available": can_mysql,
            "mysql_info": mysql_info,
            "mysql_config": {
                "host": self.mysql_config["host"],
                "port": self.mysql_config["port"],
                "user": self.mysql_config["user"],
                "database": self.mysql_config["database"]
            },
            "sqlite_file": self.sqlite_path,
            "table_stats": self.get_table_counts()
        }

    def get_table_counts(self) -> Dict[str, int]:
        tables = ["departments", "instructors", "programmes", "trainees", "enrollments", "certificates", "audit_logs"]
        stats = {}
        for t in tables:
            try:
                res = self.query(f"SELECT COUNT(*) as c FROM {t};", fetch_all=False)
                stats[t] = res["c"] if res else 0
            except Exception:
                stats[t] = 0
        return stats
