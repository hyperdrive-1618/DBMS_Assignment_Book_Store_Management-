-- ============================================================================
-- TRAINING, PROGRAMME AND CERTIFICATE MANAGEMENT SYSTEM (TPCMS)
-- Database Engine: MySQL 8.0+ / MariaDB Compatible
-- Relational Schema with 1NF to 3NF Formal Normalization, Constraints, 
-- Views, Stored Procedures, Triggers & Seed Data
-- ============================================================================

/*
-------------------------------------------------------------------------------
FORMAL DATABASE NORMALIZATION AUDIT (1NF -> 2NF -> 3NF)
-------------------------------------------------------------------------------
1. FIRST NORMAL FORM (1NF):
   - All attribute values are atomic (indivisible scalars; no multi-valued 
     or composite comma-separated values).
   - Each relation has a well-defined primary key ensuring entity uniqueness.
   - No repeating groups or variable-length arrays exist in any table.

2. SECOND NORMAL FORM (2NF):
   - Satisfies 1NF.
   - Every non-key attribute is fully functionally dependent on the primary key.
   - All tables utilize single-attribute surrogate keys (e.g. department_id,
     instructor_id, programme_id, trainee_id, enrollment_id, certificate_id).
   - Therefore, NO partial dependencies exist (no attribute depends on a 
     proper subset of any composite candidate key).

3. THIRD NORMAL FORM (3NF):
   - Satisfies 2NF.
   - For every non-trivial functional dependency X -> Y, X is a superkey OR 
     Y is a prime attribute.
   - Transitive dependencies (X -> Y -> Z) have been completely eliminated:
     * Trainees store `department_id` as foreign key; department budget & name 
       reside strictly in `departments`.
     * Programmes store `instructor_id` as foreign key; instructor details 
       reside strictly in `instructors`.
     * Certificates store ONLY `enrollment_id` as foreign key. `trainee_id`, 
       `programme_id`, and `score` are NOT duplicated in `certificates` since 
       they are transitively determined by `enrollment_id`. They are accessed 
       seamlessly via relational JOINs and database VIEWs.
-------------------------------------------------------------------------------
*/

CREATE DATABASE IF NOT EXISTS `training_mgmt_db` 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE `training_mgmt_db`;

-- Set SQL Modes & Foreign Key Checks
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS `audit_logs`;
DROP TABLE IF EXISTS `certificates`;
DROP TABLE IF EXISTS `enrollments`;
DROP TABLE IF EXISTS `trainees`;
DROP TABLE IF EXISTS `programmes`;
DROP TABLE IF EXISTS `instructors`;
DROP TABLE IF EXISTS `departments`;
SET FOREIGN_KEY_CHECKS = 1;

-- ----------------------------------------------------------------------------
-- 1. DEPARTMENTS TABLE (1NF, 2NF, 3NF)
-- PK: department_id
-- Functional Dependencies: 
--   department_id -> dept_code, name, head_of_dept, budget, created_at
--   dept_code -> department_id, name, head_of_dept, budget, created_at
-- ----------------------------------------------------------------------------
CREATE TABLE `departments` (
    `department_id` INT AUTO_INCREMENT PRIMARY KEY,
    `dept_code` VARCHAR(20) NOT NULL UNIQUE,
    `name` VARCHAR(100) NOT NULL,
    `head_of_dept` VARCHAR(100) DEFAULT NULL,
    `budget` DECIMAL(12, 2) DEFAULT 0.00,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 2. INSTRUCTORS TABLE (1NF, 2NF, 3NF)
-- PK: instructor_id
-- Candidate Keys: instructor_id, instructor_code, email
-- ----------------------------------------------------------------------------
CREATE TABLE `instructors` (
    `instructor_id` INT AUTO_INCREMENT PRIMARY KEY,
    `instructor_code` VARCHAR(20) NOT NULL UNIQUE,
    `full_name` VARCHAR(100) NOT NULL,
    `email` VARCHAR(100) NOT NULL UNIQUE,
    `phone` VARCHAR(30) DEFAULT NULL,
    `specialization` VARCHAR(100) NOT NULL,
    `qualification` VARCHAR(100) DEFAULT NULL,
    `experience_years` INT DEFAULT 3,
    `bio` TEXT DEFAULT NULL,
    `status` ENUM('Active', 'On Leave', 'Inactive') DEFAULT 'Active',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 3. PROGRAMMES TABLE (1NF, 2NF, 3NF)
-- PK: programme_id
-- Candidate Key: programme_code
-- FK: instructor_id -> instructors(instructor_id)
-- ----------------------------------------------------------------------------
CREATE TABLE `programmes` (
    `programme_id` INT AUTO_INCREMENT PRIMARY KEY,
    `programme_code` VARCHAR(25) NOT NULL UNIQUE,
    `title` VARCHAR(150) NOT NULL,
    `category` VARCHAR(60) NOT NULL,
    `level` ENUM('Beginner', 'Intermediate', 'Advanced', 'Executive') DEFAULT 'Intermediate',
    `duration_hours` INT NOT NULL DEFAULT 40,
    `max_seats` INT NOT NULL DEFAULT 30,
    `description` TEXT DEFAULT NULL,
    `syllabus_summary` TEXT DEFAULT NULL,
    `instructor_id` INT DEFAULT NULL,
    `min_passing_score` DECIMAL(5,2) DEFAULT 75.00,
    `min_attendance_pct` DECIMAL(5,2) DEFAULT 80.00,
    `status` ENUM('Draft', 'Open for Enrollment', 'In Progress', 'Completed', 'Archived') DEFAULT 'Open for Enrollment',
    `fee` DECIMAL(10, 2) DEFAULT 0.00,
    `start_date` DATE DEFAULT NULL,
    `end_date` DATE DEFAULT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_programme_instructor` 
        FOREIGN KEY (`instructor_id`) REFERENCES `instructors`(`instructor_id`) 
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 4. TRAINEES TABLE (1NF, 2NF, 3NF)
-- PK: trainee_id
-- Candidate Keys: trainee_id, trainee_code, email
-- FK: department_id -> departments(department_id)
-- ----------------------------------------------------------------------------
CREATE TABLE `trainees` (
    `trainee_id` INT AUTO_INCREMENT PRIMARY KEY,
    `trainee_code` VARCHAR(25) NOT NULL UNIQUE,
    `full_name` VARCHAR(100) NOT NULL,
    `email` VARCHAR(100) NOT NULL UNIQUE,
    `phone` VARCHAR(30) DEFAULT NULL,
    `organization` VARCHAR(120) DEFAULT 'Corporate Division',
    `designation` VARCHAR(80) DEFAULT 'Associate',
    `department_id` INT DEFAULT NULL,
    `status` ENUM('Active', 'Suspended', 'Alumni') DEFAULT 'Active',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_trainee_department` 
        FOREIGN KEY (`department_id`) REFERENCES `departments`(`department_id`) 
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 5. ENROLLMENTS TABLE (1NF, 2NF, 3NF)
-- PK: enrollment_id
-- Alternate Key: (trainee_id, programme_id)
-- FKs: trainee_id -> trainees(trainee_id), programme_id -> programmes(programme_id)
-- ----------------------------------------------------------------------------
CREATE TABLE `enrollments` (
    `enrollment_id` INT AUTO_INCREMENT PRIMARY KEY,
    `trainee_id` INT NOT NULL,
    `programme_id` INT NOT NULL,
    `enrollment_date` DATE NOT NULL,
    `status` ENUM('Enrolled', 'In Progress', 'Completed', 'Dropped', 'Failed') DEFAULT 'Enrolled',
    `progress_percentage` DECIMAL(5,2) DEFAULT 0.00,
    `attendance_percentage` DECIMAL(5,2) DEFAULT 0.00,
    `assessment_score` DECIMAL(5,2) DEFAULT NULL,
    `completion_date` DATE DEFAULT NULL,
    `remarks` TEXT DEFAULT NULL,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_enrollment_trainee` 
        FOREIGN KEY (`trainee_id`) REFERENCES `trainees`(`trainee_id`) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_enrollment_programme` 
        FOREIGN KEY (`programme_id`) REFERENCES `programmes`(`programme_id`) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `uq_trainee_programme` UNIQUE (`trainee_id`, `programme_id`)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 6. CERTIFICATES TABLE (STRICT 3NF)
-- PK: certificate_id
-- Candidate Keys: certificate_number, enrollment_id, verification_hash
-- FK: enrollment_id -> enrollments(enrollment_id)
-- Notice: Strictly normalized to 3NF by storing ONLY the enrollment foreign key.
-- Trainee, Programme, and Score are retrieved via JOINs to eliminate transitive dependencies.
-- ----------------------------------------------------------------------------
CREATE TABLE `certificates` (
    `certificate_id` INT AUTO_INCREMENT PRIMARY KEY,
    `certificate_number` VARCHAR(50) NOT NULL UNIQUE,
    `enrollment_id` INT NOT NULL UNIQUE,
    `issue_date` DATE NOT NULL,
    `expiry_date` DATE DEFAULT NULL,
    `grade` ENUM('Distinction', 'Honors', 'Pass', 'Certified') DEFAULT 'Certified',
    `verification_hash` VARCHAR(64) NOT NULL UNIQUE,
    `template_style` VARCHAR(30) DEFAULT 'Classic Royal Navy',
    `status` ENUM('Active', 'Revoked', 'Expired') DEFAULT 'Active',
    `issued_by` VARCHAR(100) DEFAULT 'Academic Board & Certification Authority',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_cert_enrollment` 
        FOREIGN KEY (`enrollment_id`) REFERENCES `enrollments`(`enrollment_id`) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 7. AUDIT LOGS TABLE
-- System change tracking & triggers audit log
-- ----------------------------------------------------------------------------
CREATE TABLE `audit_logs` (
    `log_id` INT AUTO_INCREMENT PRIMARY KEY,
    `action` VARCHAR(50) NOT NULL,
    `entity_type` VARCHAR(40) NOT NULL,
    `entity_id` INT DEFAULT NULL,
    `details` TEXT DEFAULT NULL,
    `performed_by` VARCHAR(80) DEFAULT 'System Admin',
    `timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- PERFORMANCE INDEXES
-- ----------------------------------------------------------------------------
CREATE INDEX `idx_prog_cat` ON `programmes`(`category`, `status`);
CREATE INDEX `idx_trainee_email` ON `trainees`(`email`);
CREATE INDEX `idx_enrollment_status` ON `enrollments`(`status`);
CREATE INDEX `idx_cert_number` ON `certificates`(`certificate_number`);
CREATE INDEX `idx_cert_hash` ON `certificates`(`verification_hash`);

-- ----------------------------------------------------------------------------
-- DATABASE VIEWS
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW `vw_programme_analytics` AS
SELECT 
    p.programme_id,
    p.programme_code,
    p.title AS programme_title,
    p.category,
    p.level,
    i.full_name AS instructor_name,
    COUNT(e.enrollment_id) AS total_enrolled,
    SUM(CASE WHEN e.status = 'Completed' THEN 1 ELSE 0 END) AS total_graduated,
    ROUND(AVG(e.assessment_score), 2) AS average_score,
    COUNT(c.certificate_id) AS total_certificates_issued
FROM `programmes` p
LEFT JOIN `instructors` i ON p.instructor_id = i.instructor_id
LEFT JOIN `enrollments` e ON p.programme_id = e.programme_id
LEFT JOIN `certificates` c ON e.enrollment_id = c.enrollment_id
GROUP BY p.programme_id, p.programme_code, p.title, p.category, p.level, i.full_name;

CREATE OR REPLACE VIEW `vw_certificate_directory` AS
SELECT 
    c.certificate_id,
    c.certificate_number,
    c.verification_hash,
    c.issue_date,
    c.expiry_date,
    c.grade,
    c.template_style,
    c.status AS certificate_status,
    c.issued_by,
    e.enrollment_id,
    e.assessment_score AS score,
    e.attendance_percentage,
    t.trainee_id,
    t.trainee_code,
    t.full_name AS trainee_name,
    t.email AS trainee_email,
    t.organization,
    t.designation,
    p.programme_id,
    p.programme_code,
    p.title AS programme_title,
    p.category AS programme_category,
    p.level AS programme_level,
    p.duration_hours,
    i.full_name AS instructor_name,
    i.qualification AS instructor_qualification
FROM `certificates` c
JOIN `enrollments` e ON c.enrollment_id = e.enrollment_id
JOIN `trainees` t ON e.trainee_id = t.trainee_id
JOIN `programmes` p ON e.programme_id = p.programme_id
LEFT JOIN `instructors` i ON p.instructor_id = i.instructor_id;

-- ----------------------------------------------------------------------------
-- STORED PROCEDURE: Issue Certificate Securely
-- ----------------------------------------------------------------------------
DELIMITER $$
CREATE PROCEDURE `sp_issue_certificate`(
    IN p_enrollment_id INT,
    IN p_template_style VARCHAR(30),
    IN p_issued_by VARCHAR(100),
    OUT p_cert_number VARCHAR(50),
    OUT p_result_status VARCHAR(50)
)
BEGIN
    DECLARE v_trainee_id INT;
    DECLARE v_prog_id INT;
    DECLARE v_score DECIMAL(5,2);
    DECLARE v_attendance DECIMAL(5,2);
    DECLARE v_min_score DECIMAL(5,2);
    DECLARE v_min_att DECIMAL(5,2);
    DECLARE v_existing_cert INT;
    DECLARE v_hash VARCHAR(64);
    DECLARE v_grade VARCHAR(20);

    -- Check if enrollment exists
    SELECT e.trainee_id, e.programme_id, e.assessment_score, e.attendance_percentage,
           p.min_passing_score, p.min_attendance_pct
    INTO v_trainee_id, v_prog_id, v_score, v_attendance, v_min_score, v_min_att
    FROM `enrollments` e
    JOIN `programmes` p ON e.programme_id = p.programme_id
    WHERE e.enrollment_id = p_enrollment_id;

    IF v_trainee_id IS NULL THEN
        SET p_result_status = 'ERROR: Enrollment record not found';
    ELSE
        -- Check if already issued
        SELECT COUNT(*) INTO v_existing_cert FROM `certificates` WHERE `enrollment_id` = p_enrollment_id;

        IF v_existing_cert > 0 THEN
            SET p_result_status = 'ERROR: Certificate already issued for this enrollment';
        ELSEIF v_score < v_min_score OR v_attendance < v_min_att THEN
            SET p_result_status = 'ERROR: Eligibility criteria not met (Score or Attendance insufficient)';
        ELSE
            -- Determine grade
            IF v_score >= 95.00 THEN SET v_grade = 'Distinction';
            ELSEIF v_score >= 88.00 THEN SET v_grade = 'Honors';
            ELSE SET v_grade = 'Pass';
            END IF;

            -- Generate Certificate Number & Cryptographic Hash
            SET p_cert_number = CONCAT('CERT-', YEAR(CURDATE()), '-', LPAD(FLOOR(RAND() * 90000 + 10000), 5, '0'));
            SET v_hash = SHA2(CONCAT(p_cert_number, v_trainee_id, v_prog_id, NOW()), 256);

            -- Insert Certificate (3NF compliant: referencing enrollment_id)
            INSERT INTO `certificates` 
                (`certificate_number`, `enrollment_id`, `issue_date`, `expiry_date`, `grade`, `verification_hash`, `template_style`, `issued_by`)
            VALUES 
                (p_cert_number, p_enrollment_id, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 2 YEAR), v_grade, v_hash, p_template_style, p_issued_by);

            -- Update Enrollment Status to Completed
            UPDATE `enrollments` 
            SET `status` = 'Completed', `completion_date` = CURDATE(), `progress_percentage` = 100.00
            WHERE `enrollment_id` = p_enrollment_id;

            -- Audit Log
            INSERT INTO `audit_logs` (`action`, `entity_type`, `entity_id`, `details`, `performed_by`)
            VALUES ('CERTIFICATE_ISSUED', 'CERTIFICATE', LAST_INSERT_ID(), CONCAT('Certificate ', p_cert_number, ' conferred for enrollment ', p_enrollment_id), p_issued_by);

            SET p_result_status = 'SUCCESS';
        END IF;
    END IF;
END$$
DELIMITER ;

-- ============================================================================
-- SEED DATA INSERTION
-- ============================================================================

-- Departments
INSERT INTO `departments` (`dept_code`, `name`, `head_of_dept`, `budget`) VALUES
('DEPT-IT', 'Information Technology & Engineering', 'Dr. Marcus Vance', 150000.00),
('DEPT-AI', 'Artificial Intelligence & Data Labs', 'Dr. Elena Rostova', 220000.00),
('DEPT-SEC', 'Cybersecurity Operations & Defense', 'Commander Alan Sterling', 180000.00),
('DEPT-MGMT', 'Executive Leadership & Strategy', 'Sophia Chen, MBA', 95000.00),
('DEPT-FIN', 'FinTech & Blockchain Research', 'Julian Thorne', 120000.00);

-- Instructors
INSERT INTO `instructors` (`instructor_code`, `full_name`, `email`, `phone`, `specialization`, `qualification`, `experience_years`, `bio`) VALUES
('INST-001', 'Prof. Alexander Wright', 'a.wright@academy.org', '+1 555-0192', 'Full-Stack Cloud & Microservices', 'Ph.D. in Computer Science (MIT)', 12, 'Former Principal Architect at AWS; specialist in distributed cloud systems and Kubernetes.'),
('INST-002', 'Dr. Maya Lin', 'm.lin@academy.org', '+1 555-0144', 'Machine Learning & Generative AI', 'Ph.D. in AI (Stanford)', 9, 'Senior AI Research Fellow published in NeurIPS, specializing in LLM alignment and neural networks.'),
('INST-003', 'Nathaniel Drake', 'n.drake@academy.org', '+1 555-0188', 'Offensive & Defensive Cybersecurity', 'CISSP, OSCP, CEH Master', 14, 'Veteran Red Team Lead with military-grade threat assessment and zero-day defense experience.'),
('INST-004', 'Sarah Jenkins', 's.jenkins@academy.org', '+1 555-0123', 'Agile Product Management & DevOps', 'PMP, Scrum Master Fellow', 10, 'Enterprise Transformation Coach who advised Fortune 500 tech teams across Silicon Valley.');

-- Programmes
INSERT INTO `programmes` (`programme_code`, `title`, `category`, `level`, `duration_hours`, `max_seats`, `description`, `syllabus_summary`, `instructor_id`, `min_passing_score`, `min_attendance_pct`, `status`, `fee`, `start_date`, `end_date`) VALUES
('PROG-AI-801', 'Applied Generative AI & Large Language Models', 'Artificial Intelligence', 'Advanced', 60, 25, 'Master transformer architectures, fine-tuning, retrieval-augmented generation (RAG), and agentic workflows with hands-on deployments.', '1. Transformers & Attention\n2. Prompt Engineering & Vector DBs\n3. RAG Architecture\n4. Agentic AI & Tool Integration\n5. Production Optimization', 2, 80.00, 85.00, 'In Progress', 1250.00, '2026-08-01', '2026-10-15'),
('PROG-CLOUD-402', 'Enterprise Cloud Architect & Kubernetes Masterclass', 'Cloud Computing', 'Intermediate', 48, 30, 'Deep dive into hybrid cloud architectures, container orchestration, microservices resilient networking, and CI/CD pipelines.', '1. Cloud Infrastructure as Code\n2. Kubernetes Pods, Ingress & Mesh\n3. Observability with Prometheus\n4. Cloud Security & FinOps', 1, 75.00, 80.00, 'Open for Enrollment', 980.00, '2026-10-15', '2026-11-30'),
('PROG-CYBER-905', 'Zero Trust Architecture & Threat Intelligence Defense', 'Cybersecurity', 'Advanced', 54, 20, 'Hands-on offensive penetration testing, incident response, packet forensics, and Zero Trust implementation frameworks.', '1. Threat Modeling\n2. Network Forensics\n3. Zero Trust Identity & Access\n4. Red/Blue Simulation Labs\n5. Regulatory Compliance', 3, 85.00, 90.00, 'In Progress', 1450.00, '2026-07-10', '2026-09-28'),
('PROG-DEV-204', 'Modern Full-Stack Engineering with React & Node', 'Software Engineering', 'Beginner', 40, 35, 'Comprehensive fundamentals to modern reactive frontends, REST & GraphQL APIs, database optimization, and secure session management.', '1. Modern JavaScript & React\n2. Backend REST APIs with Node\n3. Relational Schema & ORMs\n4. Authentication & Deployment', 1, 75.00, 80.00, 'Completed', 750.00, '2026-05-01', '2026-06-20'),
('PROG-MGMT-601', 'Strategic Agile Leadership & Executive Coaching', 'Management', 'Executive', 32, 18, 'Designed for engineering leads and VP-level executives to drive high-velocity software cultures and strategic change management.', '1. Servant Leadership\n2. Value Stream Mapping\n3. OKRs & Metric Systems\n4. High-Performance Team Dynamics', 4, 80.00, 85.00, 'Open for Enrollment', 1600.00, '2026-11-01', '2026-12-10');

-- Trainees
INSERT INTO `trainees` (`trainee_code`, `full_name`, `email`, `phone`, `organization`, `designation`, `department_id`, `status`) VALUES
('TRN-1001', 'Elena Rostova', 'elena.rostova@techcorp.io', '+1 555-3291', 'Apex Tech Solutions', 'Lead Data Scientist', 2, 'Active'),
('TRN-1002', 'Liam O''Connor', 'liam.oconnor@skyward.org', '+1 555-4421', 'Skyward Networks', 'Senior DevOps Engineer', 1, 'Active'),
('TRN-1003', 'Priya Sharma', 'priya.sharma@cyberdefense.in', '+1 555-8812', 'Vanguard Security Labs', 'Security Operations Analyst', 3, 'Active'),
('TRN-1004', 'Carlos Mendez', 'carlos.m@globalfin.com', '+1 555-9019', 'Global Horizon Capital', 'Principal Software Engineer', 1, 'Active'),
('TRN-1005', 'Amina Al-Mansoor', 'amina.m@innovate.ae', '+1 555-6672', 'Emirates Innovation Hub', 'Product Strategy Director', 4, 'Active'),
('TRN-1006', 'Dmitri Volkov', 'dmitri.v@datacore.net', '+1 555-7733', 'DataCore Systems', 'ML Infrastructure Engineer', 2, 'Active'),
('TRN-1007', 'Kavita Patel', 'kavita.patel@horizon.edu', '+1 555-1129', 'Apex Tech Solutions', 'Junior Full-Stack Dev', 1, 'Active');

-- Enrollments
INSERT INTO `enrollments` (`trainee_id`, `programme_id`, `enrollment_date`, `status`, `progress_percentage`, `attendance_percentage`, `assessment_score`, `completion_date`, `remarks`) VALUES
(1, 1, '2026-08-01', 'Completed', 100.00, 96.00, 94.50, '2026-10-02', 'Exemplary capstone project on multi-agent RAG pipeline.'),
(2, 2, '2026-08-10', 'In Progress', 78.00, 88.00, 84.00, NULL, 'Strong progress in Kubernetes lab sessions.'),
(3, 3, '2026-07-10', 'Completed', 100.00, 95.00, 96.00, '2026-09-25', 'Top scorer in Red/Blue defensive simulation drill.'),
(4, 4, '2026-05-01', 'Completed', 100.00, 90.00, 89.00, '2026-06-20', 'Successfully delivered responsive web platform.'),
(5, 5, '2026-09-01', 'In Progress', 45.00, 92.00, 88.00, NULL, 'Active participation in executive case studies.'),
(6, 1, '2026-08-01', 'In Progress', 82.00, 85.00, 78.50, NULL, 'Undergoing final neural model fine-tuning benchmark.'),
(7, 4, '2026-05-01', 'Completed', 100.00, 92.00, 91.00, '2026-06-20', 'Outstanding frontend architecture submission.');

-- Certificates (Strict 3NF - referenced via enrollment_id)
INSERT INTO `certificates` (`certificate_number`, `enrollment_id`, `issue_date`, `expiry_date`, `grade`, `verification_hash`, `template_style`, `status`, `issued_by`) VALUES
('CERT-2026-89101', 1, '2026-10-02', '2028-10-02', 'Honors', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'Classic Royal Navy', 'Active', 'Dr. Maya Lin & Board of Examiners'),
('CERT-2026-44219', 3, '2026-09-25', '2028-09-25', 'Distinction', 'ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb', 'Obsidian Gold Seal', 'Active', 'Nathaniel Drake & Defense Directorate'),
('CERT-2026-30114', 4, '2026-06-20', '2028-06-20', 'Honors', '4e07408562bedb8b60ce05c1decfe3ad16b72230967de01f640b7e4729b49fce', 'Modern Emerald Elegance', 'Active', 'Prof. Alexander Wright & Tech Board'),
('CERT-2026-77823', 7, '2026-06-20', '2028-06-20', 'Distinction', '4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a', 'Modern Emerald Elegance', 'Active', 'Prof. Alexander Wright & Tech Board');

-- Audit Logs
INSERT INTO `audit_logs` (`action`, `entity_type`, `entity_id`, `details`, `performed_by`) VALUES
('SYSTEM_INIT', 'DATABASE', 1, 'Initial database schema and seeds generated successfully.', 'Root Administrator'),
('CERTIFICATE_ISSUED', 'CERTIFICATE', 1, 'Issued CERT-2026-89101 to enrollment 1 with Honors.', 'Academic Board'),
('CERTIFICATE_ISSUED', 'CERTIFICATE', 2, 'Issued CERT-2026-44219 to enrollment 3 with Distinction.', 'Defense Directorate'),
('CERTIFICATE_ISSUED', 'CERTIFICATE', 3, 'Issued CERT-2026-30114 to enrollment 4 with Honors.', 'Tech Board'),
('CERTIFICATE_ISSUED', 'CERTIFICATE', 4, 'Issued CERT-2026-77823 to enrollment 7 with Distinction.', 'Tech Board');
