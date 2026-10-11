# 📘 TPCMS User & Operational Instruction Manual

This manual provides a step-by-step guide for administrators, instructors, students, and evaluators using the **Training, Programme and Certificate Management System (TPCMS)**.

---

## 📑 Table of Contents
1. [Starting the System](#1-starting-the-system)
2. [Navigating the Workspace](#2-navigating-the-workspace)
3. [Managing Training Programmes](#3-managing-training-programmes)
4. [Trainee Registration & Enrollment](#4-trainee-registration--enrollment)
5. [Grading, Attendance & Progress Tracking](#5-grading-attendance--progress-tracking)
6. [Certificate Issuance & Printing](#6-certificate-issuance--printing)
7. [Public Credential Verification](#7-public-credential-verification)
8. [MySQL Server Connection & Query Console](#8-mysql-server-connection--query-console)
9. [Troubleshooting & FAQs](#9-troubleshooting--faqs)

---

## 1. Starting the System

### Option 1: Running with `./run.sh`
In your terminal, navigate to the project directory and run:
```bash
./run.sh
```
This automatically selects the virtual environment and starts the server on `http://localhost:5050`.

### Option 2: Running with Python
```bash
python3 app.py
```
Open your web browser and go to `http://localhost:5050`.

---

## 2. Navigating the Workspace

The user interface is organized into five operational areas via the left-hand sidebar:
- **📊 Dashboard**: High-level executive overview of training metrics, category distributions, recent certificates, and system audit logs.
- **🎓 Training Programmes**: Catalog of courses, capacity, level, duration, and curriculum details.
- **👥 Trainees & Batches**: Learner records, course enrollment statuses, attendance rates, and assessment marks.
- **📜 Certificates Hub**: Official repository of all granted credentials with template preview and PDF export.
- **🔍 Credential Verification**: Public registry tool to authenticate certificates using Certificate IDs or SHA-256 cryptographic hashes.
- **🗄️ MySQL Console**: In-app DBMS control panel to manage database connections and run direct SQL queries.

---

## 3. Managing Training Programmes

### Creating a New Programme
1. Click **+ Add New Programme** on the topbar or within the Programmes view.
2. In the modal:
   - **Programme Title**: Enter the course name (e.g., *Advanced Cloud Security & Microservices*).
   - **Category**: Select domain (AI, Cloud, Cybersecurity, Software Engineering, Management).
   - **Level**: Select difficulty (*Beginner*, *Intermediate*, *Advanced*, *Executive*).
   - **Assigned Instructor**: Choose a faculty lead from the dropdown.
   - **Duration**: Specify total course hours (e.g., 40).
   - **Passing Score (%)**: Minimum assessment percentage required for certification (e.g., 75%).
   - **Min Attendance (%)**: Minimum attendance percentage required (e.g., 80%).
   - **Description**: Provide course syllabus highlights and outcomes.
3. Click **Create Programme**. The programme is saved and immediately visible in the catalog.

### Filtering Programmes
- Use the **Category dropdown** to filter by domain.
- Use the **Status dropdown** to view *Open for Enrollment*, *In Progress*, or *Completed* courses.

---

## 4. Trainee Registration & Enrollment

### Registering a Trainee
1. Navigate to **Trainees & Batches** in the sidebar.
2. Click **Register Trainee**.
3. Fill in:
   - **Full Name**: e.g., *Sarah Connor*
   - **Official Email**: e.g., *sarah.c@cyberdyne.org*
   - **Phone**: Contact number
   - **Organization**: Company or university
   - **Department**: Choose from the relational department list.
4. Click **Register Trainee**.

### Enrolling in a Programme
1. Click **Enroll in Course** (or click **+ Enroll Trainee** directly on any course card).
2. Select the Trainee and the Target Programme.
3. Click **Confirm Enrollment**. The enrollment record is initialized with 0% progress and attendance.

---

## 5. Grading, Attendance & Progress Tracking

1. Navigate to **Trainees & Batches**.
2. Locate the trainee in the table and click **Grade & Progress**.
3. In the modal:
   - Adjust the **Progress Percentage (%)** (set to 100% when the course completes).
   - Update the **Attendance Percentage (%)**.
   - Enter the **Final Assessment Score (%)** (e.g., 94.5%).
   - Add optional **Instructor Remarks**.
4. Click **Save Changes**.
5. **Eligibility Automation**:
   - If the student meets or exceeds the course passing score and attendance requirement, the system automatically marks them as eligible for certification.

---

## 6. Certificate Issuance & Printing

### Issuing a Certificate
1. Go to **Certificates Hub** (or click the topbar **Issue Certificate** button).
2. Click **Issue New Certificate**.
3. The dropdown automatically filters and displays **only eligible candidates** who have satisfied attendance and passing score criteria.
4. Select the candidate, choose your preferred visual theme (*Classic Royal Navy*, *Obsidian Gold Seal*, or *Modern Emerald Elegance*), and verify the issuing authority title.
5. Click **Issue & Sign Certificate**.
6. The system automatically:
   - Generates an official Certificate ID (e.g., `CERT-2026-89101`).
   - Computes a SHA-256 cryptographic tamper-proof validation hash.
   - Determines academic honors (*Distinction* $\ge 95\%$, *Honors* $\ge 88\%$, *Pass*).
   - Marks the enrollment status as *Completed*.
   - Records an entry in `audit_logs`.
   - Opens the newly minted certificate in the viewer!

### Viewing & Printing / Exporting to PDF
1. Click **View & Print** next to any certificate record.
2. The modal displays an authentic credential layout:
   - Double ornamental gold borders and corner filigree.
   - Central watermarked security imprint.
   - Recipient name and conferred programme.
   - Metallic embossed gold foil seal displaying honors.
   - Digital signature line and authorized titles.
   - Verification token and conferral date.
3. Click **Print / Save PDF**. The print stylesheet isolates the certificate sheet and generates a high-resolution landscape A4 document suitable for framing or digital archiving.

---

## 7. Public Credential Verification

1. Navigate to **Credential Verification** (or go to `http://localhost:5050/#verify`).
2. Type or paste any Certificate ID (e.g., `CERT-2026-89101`) or SHA-256 hash.
3. Click **Verify Credential**.
4. If valid, an official green verification badge is rendered with:
   - Certified Recipient Name
   - Programme Title & Code
   - Academic Standing & Final Score
   - Conferral Date & Validity Period
   - Instruction Lead Name
   - Cryptographic SHA-256 Hash
5. If invalid or tampered with, a red **"Record Not Found"** notification is displayed.

---

## 8. MySQL Server Connection & Query Console

### Switching to MySQL Live
1. Click **MySQL Settings** in the topbar or navigate to **MySQL Console**.
2. Enter your MySQL server host (`localhost`), port (`3306`), username (`root`), password, and database name (`training_mgmt_db`).
3. Click **Test Connection**.
4. Click **Connect & Migrate**. The system executes `database/schema.sql`, builds all tables, triggers, and views, and switches live traffic to MySQL.

### Executing Raw SQL Queries
1. In the **MySQL Console** tab, locate the **DBMS SQL Query Console**.
2. Type any standard SQL statement or click one of the quick presets:
   - `SELECT * FROM programmes;`
   - `SELECT * FROM vw_programme_analytics;`
   - `SELECT c.certificate_number, t.full_name, c.grade, c.issue_date FROM certificates c JOIN enrollments e ON c.enrollment_id = e.enrollment_id JOIN trainees t ON e.trainee_id = t.trainee_id;`
3. Click **Execute SQL Statement**.
4. The system outputs a clean, monospace data table showing returned records, row count, and the active database engine.

---

## 9. Troubleshooting & FAQs

- **Q: Does the app require MySQL to be installed to demo the features?**  
  *A: No. The application features an automatic local SQLite fallback mode with identical tables and seed data, so you can test and present the full prototype immediately.*
- **Q: How do I verify my database is 1NF to 3NF compliant?**  
  *A: See the formal normalization proof section in [`README.md`](file:///Users/anirudh/Documents/GitHub/DBMS_Assignment_Book_Store_Management-/README.md) or inspect the top comments in [`database/schema.sql`](file:///Users/anirudh/Documents/GitHub/DBMS_Assignment_Book_Store_Management-/database/schema.sql).*
- **Q: How do I reset the seed data?**  
  *A: In local mode, simply delete `database/tpcms_local.db` and restart `app.py`. In MySQL mode, click "Connect & Migrate" or re-run `schema.sql`.*
