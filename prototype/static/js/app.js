/**
 * TRAINING, PROGRAMME AND CERTIFICATE MANAGEMENT SYSTEM (TPCMS)
 * Professional Enterprise Frontend Application Script
 */

// Application State
const state = {
  activeTab: 'dashboard',
  dashboardData: null,
  programmes: [],
  trainees: [],
  enrollments: [],
  certificates: [],
  instructors: [],
  departments: [],
  dbStatus: null
};

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initModals();
  initForms();
  initDbConsole();
  initGlobalSearch();

  // Initial Data Fetch
  loadDbStatus();
  loadDashboard();
  loadProgrammes();
  loadTrainees();
  loadEnrollments();
  loadCertificates();
  loadMetadata();

  // Check if URL has /verify query
  checkUrlForVerification();
});

// -----------------------------------------------------------------------------
// Navigation & Tab Switching
// -----------------------------------------------------------------------------
function initNavigation() {
  const navLinks = document.querySelectorAll('.nav-link');
  const headings = {
    'dashboard': 'Executive Dashboard',
    'programmes': 'Training Programmes & Catalog',
    'trainees': 'Trainees & Enrollment Batches',
    'certificates': 'Official Certificates Hub',
    'verify': 'Public Credential Verification',
    'database': 'MySQL Database Console'
  };

  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const targetTab = link.getAttribute('data-tab');
      navigateToTab(targetTab);
    });
  });

  // Quick Action Buttons in Topbar
  document.getElementById('btn-quick-create-prog')?.addEventListener('click', () => {
    openModal('modal-add-programme');
  });

  document.getElementById('btn-quick-issue-cert')?.addEventListener('click', () => {
    openIssueCertModal();
  });

  document.getElementById('btn-open-mysql-modal')?.addEventListener('click', () => {
    openModal('modal-mysql-config');
  });

  document.getElementById('db-status-trigger')?.addEventListener('click', () => {
    navigateToTab('database');
  });
}

function navigateToTab(tabId) {
  state.activeTab = tabId;

  // Update nav links
  document.querySelectorAll('.nav-link').forEach(l => {
    l.classList.toggle('active', l.getAttribute('data-tab') === tabId);
  });

  // Update tab panes
  document.querySelectorAll('.tab-pane').forEach(pane => {
    pane.classList.toggle('active', pane.id === `tab-${tabId}`);
  });

  // Update Page Title
  const titles = {
    'dashboard': 'Executive Dashboard',
    'programmes': 'Training Programmes & Catalog',
    'trainees': 'Trainees & Enrollment Batches',
    'certificates': 'Official Certificates Hub',
    'verify': 'Public Credential Verification',
    'database': 'MySQL Database Console'
  };
  const titleEl = document.getElementById('page-title-heading');
  if (titleEl) titleEl.textContent = titles[tabId] || 'TPCMS Console';

  // Refresh relevant tab data
  if (tabId === 'dashboard') loadDashboard();
  if (tabId === 'programmes') loadProgrammes();
  if (tabId === 'trainees') loadEnrollments();
  if (tabId === 'certificates') loadCertificates();
  if (tabId === 'database') loadDbStatus();
}

// -----------------------------------------------------------------------------
// Toast Notifications
// -----------------------------------------------------------------------------
function showToast(message, type = 'success') {
  const container = document.getElementById('toast-box');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span style="font-weight: 700;">${type === 'success' ? '✓' : '⚠'}</span>
    <span>${message}</span>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// -----------------------------------------------------------------------------
// Modals Management
// -----------------------------------------------------------------------------
function initModals() {
  document.querySelectorAll('.modal-overlay').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.remove('active');
      }
    });
  });

  // Specific Modal Openers
  document.getElementById('btn-add-programme-modal')?.addEventListener('click', () => openModal('modal-add-programme'));
  document.getElementById('btn-add-trainee-modal')?.addEventListener('click', () => openModal('modal-add-trainee'));
  document.getElementById('btn-enroll-trainee-modal')?.addEventListener('click', () => openModal('modal-enroll-trainee'));
  document.getElementById('btn-issue-cert-modal')?.addEventListener('click', () => openIssueCertModal());
}

function openModal(modalId) {
  const m = document.getElementById(modalId);
  if (m) m.classList.add('active');
}

function closeModal(modalId) {
  const m = document.getElementById(modalId);
  if (m) m.classList.remove('active');
}

// -----------------------------------------------------------------------------
// API Integration & Data Loaders
// -----------------------------------------------------------------------------

// 1. Dashboard
async function loadDashboard() {
  try {
    const res = await fetch('/api/dashboard');
    const json = await res.json();
    if (json.status !== 'success') return;

    const data = json.data;
    state.dashboardData = data;

    // Set KPI Values
    document.getElementById('kpi-trainees').textContent = data.total_trainees;
    document.getElementById('kpi-programmes').textContent = data.total_programmes;
    document.getElementById('kpi-active-prog-label').textContent = `${data.active_programmes} Active & Open Courses`;
    document.getElementById('kpi-certificates').textContent = data.total_certificates;
    document.getElementById('kpi-completion-rate').textContent = `${data.completion_rate}%`;
    document.getElementById('kpi-avg-score-label').textContent = `Avg Assessment Score: ${data.avg_assessment_score}%`;

    // Render Categories
    renderCategoryBars(data.categories || []);

    // Render Recent Certificates
    renderRecentCertificates(data.recent_certificates || []);

    // Render Audit Logs
    renderAuditLogs(data.recent_logs || []);

    // Update DB engine status in pill
    updateDbPill(data.engine, data.mysql_host, data.mysql_db);
  } catch (err) {
    console.error('Failed to load dashboard:', err);
  }
}

function renderCategoryBars(categories) {
  const container = document.getElementById('category-bars-container');
  if (!container) return;

  if (categories.length === 0) {
    container.innerHTML = '<div style="color: var(--text-muted); font-size: 0.85rem;">No category data recorded.</div>';
    return;
  }

  const total = categories.reduce((sum, c) => sum + c.count, 0) || 1;
  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4'];

  container.innerHTML = categories.map((cat, idx) => {
    const pct = Math.round((cat.count / total) * 100);
    const color = colors[idx % colors.length];
    return `
      <div>
        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 4px;">
          <span style="font-weight: 600;">${cat.category}</span>
          <span style="color: var(--text-muted);">${cat.count} course(s) (${pct}%)</span>
        </div>
        <div class="progress-bar-wrap" style="height: 8px;">
          <div class="progress-bar-fill" style="width: ${pct}%; background: ${color};"></div>
        </div>
      </div>
    `;
  }).join('');
}

function renderRecentCertificates(certs) {
  const container = document.getElementById('dashboard-recent-certs');
  if (!container) return;

  if (certs.length === 0) {
    container.innerHTML = '<div style="color: var(--text-muted); font-size: 0.85rem;">No certificates issued yet.</div>';
    return;
  }

  container.innerHTML = certs.map(c => `
    <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; background: rgba(15, 23, 42, 0.6); border-radius: var(--radius-md); border: 1px solid var(--border-subtle);">
      <div>
        <div style="font-weight: 700; font-size: 0.9rem;">${c.trainee_name}</div>
        <div style="font-size: 0.78rem; color: var(--text-muted);">${c.programme_title}</div>
      </div>
      <div style="display: flex; align-items: center; gap: 10px;">
        <span class="badge ${c.grade === 'Distinction' ? 'badge-amber' : 'badge-blue'}">${c.grade} (${c.score}%)</span>
        <button class="btn btn-secondary btn-sm" onclick="viewCertificateByNumber('${c.certificate_number}')">View</button>
      </div>
    </div>
  `).join('');
}

function renderAuditLogs(logs) {
  const tbody = document.getElementById('dashboard-audit-tbody');
  if (!tbody) return;

  if (logs.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No audit events recorded.</td></tr>';
    return;
  }

  tbody.innerHTML = logs.map(l => `
    <tr>
      <td><span class="badge badge-purple font-mono">${l.action}</span></td>
      <td><strong>${l.entity_type}</strong></td>
      <td style="color: var(--text-muted);">${l.details}</td>
      <td><span class="badge badge-blue">${l.performed_by}</span></td>
      <td class="font-mono" style="font-size: 0.78rem; color: var(--text-subtle);">${l.timestamp}</td>
    </tr>
  `).join('');
}

// 2. Programmes Tab
async function loadProgrammes() {
  const cat = document.getElementById('filter-prog-category')?.value || 'All';
  const status = document.getElementById('filter-prog-status')?.value || 'All';

  try {
    const url = `/api/programmes?category=${encodeURIComponent(cat)}&status=${encodeURIComponent(status)}`;
    const res = await fetch(url);
    const json = await res.json();
    if (json.status !== 'success') return;

    state.programmes = json.data;
    renderProgrammesGrid(json.data);
  } catch (err) {
    console.error('Failed to load programmes:', err);
  }
}

function renderProgrammesGrid(programmes) {
  const grid = document.getElementById('programmes-card-grid');
  if (!grid) return;

  if (programmes.length === 0) {
    grid.innerHTML = '<div style="color: var(--text-muted); padding: 20px; grid-column: span 3;">No training programmes found matching criteria.</div>';
    return;
  }

  grid.innerHTML = programmes.map(p => `
    <div class="course-card">
      <div>
        <div class="course-header">
          <span class="course-code">${p.programme_code}</span>
          <span class="badge ${p.status === 'Completed' ? 'badge-purple' : (p.status === 'In Progress' ? 'badge-blue' : 'badge-green')}">${p.status}</span>
        </div>
        <h3 class="course-title">${p.title}</h3>
        <p class="course-desc">${p.description || 'Comprehensive curriculum with hands-on enterprise benchmarks.'}</p>
      </div>

      <div>
        <div class="course-meta">
          <span>Instructor: <strong>${p.instructor_name || 'Assigned Lead'}</strong></span>
          <span>${p.duration_hours} Hours</span>
        </div>

        <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 6px;">
          <span style="color: var(--text-muted);">Enrollment: <strong>${p.enrolled_count || 0}/${p.max_seats}</strong></span>
          <span style="color: var(--accent-amber);">Passing: <strong>${p.min_passing_score}%</strong></span>
        </div>

        <div class="progress-bar-wrap" style="margin-bottom: 14px;">
          <div class="progress-bar-fill" style="width: ${Math.min(100, Math.round(((p.enrolled_count || 0) / p.max_seats) * 100))}%;"></div>
        </div>

        <div style="display: flex; gap: 8px;">
          <button class="btn btn-secondary btn-sm" style="flex: 1;" onclick="openEnrollForProgramme(${p.programme_id})">
            + Enroll Trainee
          </button>
          <button class="btn btn-primary btn-sm" onclick="navigateToTraineesForProg(${p.programme_id})">
            Learners (${p.enrolled_count || 0})
          </button>
        </div>
      </div>
    </div>
  `).join('');
}

// 3. Trainees & Enrollments
async function loadEnrollments() {
  const statusFilter = document.getElementById('enrollment-status-filter')?.value || 'All';
  try {
    const res = await fetch(`/api/enrollments?status=${encodeURIComponent(statusFilter)}`);
    const json = await res.json();
    if (json.status !== 'success') return;

    state.enrollments = json.data;
    renderEnrollmentsTable(json.data);
  } catch (err) {
    console.error('Failed to load enrollments:', err);
  }
}

function renderEnrollmentsTable(enrollments) {
  const tbody = document.getElementById('enrollments-table-tbody');
  if (!tbody) return;

  const search = document.getElementById('trainee-filter-search')?.value.toLowerCase() || '';
  const filtered = enrollments.filter(e => {
    return e.trainee_name.toLowerCase().includes(search) ||
           e.trainee_code.toLowerCase().includes(search) ||
           e.programme_title.toLowerCase().includes(search) ||
           (e.organization && e.organization.toLowerCase().includes(search));
  });

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 20px;">No trainee enrollment records found.</td></tr>';
    return;
  }

  tbody.innerHTML = filtered.map(e => {
    const isEligible = (e.assessment_score >= e.min_passing_score) && (e.attendance_percentage >= e.min_attendance_pct);
    const hasCert = Boolean(e.certificate_number);

    return `
      <tr>
        <td>
          <div style="font-weight: 700;">${e.trainee_name}</div>
          <div style="font-size: 0.75rem; color: var(--text-muted);">${e.trainee_code} • ${e.organization || 'Corporate'}</div>
        </td>
        <td>
          <div style="font-weight: 600;">${e.programme_title}</div>
          <div class="font-mono" style="font-size: 0.75rem; color: var(--accent-cyan);">${e.programme_code}</div>
        </td>
        <td style="min-width: 120px;">
          <div style="display: flex; justify-content: space-between; font-size: 0.78rem;">
            <span>${e.progress_percentage}%</span>
          </div>
          <div class="progress-bar-wrap">
            <div class="progress-bar-fill ${e.progress_percentage >= 100 ? 'success' : ''}" style="width: ${e.progress_percentage}%;"></div>
          </div>
        </td>
        <td>
          <span style="font-weight: 600; color: ${e.attendance_percentage >= e.min_attendance_pct ? 'var(--accent-emerald)' : 'var(--accent-rose)'};">
            ${e.attendance_percentage}%
          </span>
          <span style="font-size: 0.72rem; color: var(--text-subtle);"> (req ${e.min_attendance_pct}%)</span>
        </td>
        <td>
          ${e.assessment_score !== null ? `
            <span class="badge ${e.assessment_score >= e.min_passing_score ? 'badge-green' : 'badge-red'}">
              ${e.assessment_score}%
            </span>
          ` : '<span style="color: var(--text-subtle); font-style: italic;">Pending Exam</span>'}
        </td>
        <td>
          <span class="badge ${e.status === 'Completed' ? 'badge-purple' : 'badge-blue'}">${e.status}</span>
        </td>
        <td>
          <div style="display: flex; gap: 6px;">
            <button class="btn btn-secondary btn-sm" onclick="openUpdateProgressModal(${e.enrollment_id}, '${escapeQuote(e.trainee_name)}', '${escapeQuote(e.programme_title)}', ${e.progress_percentage}, ${e.attendance_percentage}, ${e.assessment_score || 0}, '${escapeQuote(e.remarks || '')}')">
              Grade & Progress
            </button>
            ${hasCert ? `
              <button class="btn btn-gold btn-sm" onclick="viewCertificateByNumber('${e.certificate_number}')">
                View Cert
              </button>
            ` : (isEligible ? `
              <button class="btn btn-primary btn-sm" onclick="quickIssueForEnrollment(${e.enrollment_id})">
                Issue Cert
              </button>
            ` : '')}
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

// 4. Certificates Hub
async function loadCertificates() {
  const statusFilter = document.getElementById('cert-status-filter')?.value || 'All';
  try {
    const res = await fetch(`/api/certificates?status=${encodeURIComponent(statusFilter)}`);
    const json = await res.json();
    if (json.status !== 'success') return;

    state.certificates = json.data;
    renderCertificatesTable(json.data);
  } catch (err) {
    console.error('Failed to load certificates:', err);
  }
}

function renderCertificatesTable(certs) {
  const tbody = document.getElementById('certificates-table-tbody');
  if (!tbody) return;

  const search = document.getElementById('cert-filter-search')?.value.toLowerCase() || '';
  const filtered = certs.filter(c => {
    return c.certificate_number.toLowerCase().includes(search) ||
           c.trainee_name.toLowerCase().includes(search) ||
           c.programme_title.toLowerCase().includes(search) ||
           c.verification_hash.toLowerCase().includes(search);
  });

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 20px;">No issued certificates found.</td></tr>';
    return;
  }

  tbody.innerHTML = filtered.map(c => `
    <tr>
      <td>
        <span class="font-mono" style="font-weight: 700; color: #fff;">${c.certificate_number}</span>
        <div class="font-mono" style="font-size: 0.72rem; color: var(--text-subtle);">${c.verification_hash.substring(0, 16)}...</div>
      </td>
      <td>
        <div style="font-weight: 700;">${c.trainee_name}</div>
        <div style="font-size: 0.75rem; color: var(--text-muted);">${c.organization || 'Corporate'}</div>
      </td>
      <td>
        <div style="font-weight: 600;">${c.programme_title}</div>
        <div style="font-size: 0.75rem; color: var(--text-muted);">${c.duration_hours} Hours • Lead: ${c.instructor_name || 'Lead Trainer'}</div>
      </td>
      <td>
        <span class="badge ${c.grade === 'Distinction' ? 'badge-amber' : (c.grade === 'Honors' ? 'badge-purple' : 'badge-blue')}">
          ${c.grade} (${c.score}%)
        </span>
      </td>
      <td class="font-mono" style="font-size: 0.82rem;">${c.issue_date}</td>
      <td><span class="badge badge-green">${c.status}</span></td>
      <td>
        <div style="display: flex; gap: 6px;">
          <button class="btn btn-gold btn-sm" onclick="viewCertificateByNumber('${c.certificate_number}')">
            View & Print
          </button>
          <button class="btn btn-secondary btn-sm" onclick="copyVerificationLink('${c.certificate_number}')" title="Copy public verification link">
            Copy Link
          </button>
        </div>
      </td>
    </tr>
  `).join('');
}

// 5. Metadata Loaders (Instructors, Departments, Trainees)
async function loadMetadata() {
  try {
    const [instRes, deptRes, trnRes] = await Promise.all([
      fetch('/api/instructors'),
      fetch('/api/departments'),
      fetch('/api/trainees')
    ]);

    const instJson = await instRes.json();
    const deptJson = await deptRes.json();
    const trnJson = await trnRes.json();

    if (instJson.status === 'success') {
      state.instructors = instJson.data;
      populateInstructorDropdowns(instJson.data);
    }
    if (deptJson.status === 'success') {
      state.departments = deptJson.data;
      populateDepartmentDropdowns(deptJson.data);
    }
    if (trnJson.status === 'success') {
      state.trainees = trnJson.data;
      populateTraineeDropdowns(trnJson.data);
    }
  } catch (err) {
    console.error('Failed to load metadata:', err);
  }
}

function loadTrainees() {
  loadMetadata();
}

function populateInstructorDropdowns(instructors) {
  const sel = document.getElementById('prog-instructor');
  if (!sel) return;
  sel.innerHTML = '<option value="">Select Instructor...</option>' + 
    instructors.map(i => `<option value="${i.instructor_id}">${i.full_name} (${i.specialization})</option>`).join('');
}

function populateDepartmentDropdowns(depts) {
  const sel = document.getElementById('trainee-dept');
  if (!sel) return;
  sel.innerHTML = '<option value="">Select Department...</option>' +
    depts.map(d => `<option value="${d.department_id}">${d.name} (${d.dept_code})</option>`).join('');
}

function populateTraineeDropdowns(trainees) {
  const sel = document.getElementById('enroll-trainee-select');
  if (!sel) return;
  sel.innerHTML = '<option value="">Select Trainee...</option>' +
    trainees.map(t => `<option value="${t.trainee_id}">${t.full_name} - ${t.email} (${t.organization})</option>`).join('');
}

// -----------------------------------------------------------------------------
// Certificate Viewer & Printing
// -----------------------------------------------------------------------------
async function viewCertificateByNumber(certNumber) {
  try {
    const res = await fetch(`/api/certificates/verify/${encodeURIComponent(certNumber)}`);
    const json = await res.json();
    if (json.status !== 'success' || !json.data) {
      showToast('Certificate details not found.', 'error');
      return;
    }

    const c = json.data;
    document.getElementById('view-cert-recipient').textContent = c.trainee_name;
    document.getElementById('view-cert-course').textContent = c.programme_title;
    document.getElementById('view-cert-grade').textContent = (c.grade || 'CERTIFIED').toUpperCase();
    document.getElementById('view-cert-inst-sig').textContent = c.instructor_name || 'Academic Director';
    document.getElementById('view-cert-id').textContent = c.certificate_number;
    document.getElementById('view-cert-date').textContent = c.issue_date;
    document.getElementById('view-cert-hash').textContent = (c.verification_hash || '').substring(0, 24) + '...';

    // Style the seal color based on grade
    const seal = document.querySelector('.cert-gold-seal');
    if (seal) {
      if (c.grade === 'Distinction') {
        seal.style.background = 'radial-gradient(circle at 30% 30%, #fbeea4 0%, #d4af37 55%, #aa7c11 100%)';
      } else {
        seal.style.background = 'radial-gradient(circle at 30% 30%, #e2e8f0 0%, #94a3b8 55%, #64748b 100%)';
      }
    }

    openModal('modal-cert-viewer');
  } catch (err) {
    showToast('Failed to open certificate viewer.', 'error');
  }
}

function copyVerificationLink(certNumber) {
  const url = `${window.location.origin}/#verify?id=${encodeURIComponent(certNumber)}`;
  navigator.clipboard.writeText(url).then(() => {
    showToast(`Verification link copied for ${certNumber}!`);
  }).catch(() => {
    prompt('Copy verification URL:', url);
  });
}

// -----------------------------------------------------------------------------
// Issue Certificate Flow
// -----------------------------------------------------------------------------
async function openIssueCertModal() {
  const sel = document.getElementById('issue-enrollment-select');
  if (!sel) return;

  sel.innerHTML = '<option value="">Loading eligible candidates...</option>';
  openModal('modal-issue-cert');

  try {
    const res = await fetch('/api/enrollments');
    const json = await res.json();
    if (json.status !== 'success') return;

    // Filter eligible: assessment_score >= min_passing_score & attendance_percentage >= min_attendance_pct & not issued yet
    const eligible = json.data.filter(e => {
      const passed = (e.assessment_score !== null && e.assessment_score >= e.min_passing_score);
      const attended = (e.attendance_percentage >= e.min_attendance_pct);
      const noCert = !e.certificate_number;
      return passed && attended && noCert;
    });

    if (eligible.length === 0) {
      sel.innerHTML = '<option value="">No eligible trainees currently pending certification.</option>';
    } else {
      sel.innerHTML = '<option value="">Select Eligible Trainee...</option>' + 
        eligible.map(e => `
          <option value="${e.enrollment_id}">
            ${e.trainee_name} - ${e.programme_title} (Score: ${e.assessment_score}%, Att: ${e.attendance_percentage}%)
          </option>
        `).join('');
    }
  } catch (err) {
    sel.innerHTML = '<option value="">Failed to load enrollment list.</option>';
  }
}

function quickIssueForEnrollment(enrollmentId) {
  openIssueCertModal().then(() => {
    const sel = document.getElementById('issue-enrollment-select');
    if (sel) sel.value = enrollmentId;
  });
}

// -----------------------------------------------------------------------------
// Credential Verification Portal
// -----------------------------------------------------------------------------
function checkUrlForVerification() {
  const hash = window.location.hash;
  if (hash.includes('verify')) {
    navigateToTab('verify');
    const params = new URLSearchParams(hash.split('?')[1]);
    const id = params.get('id');
    if (id) {
      quickVerify(id);
    }
  }
}

async function quickVerify(certId) {
  const input = document.getElementById('verify-input-query');
  if (input) input.value = certId;
  await runVerification(certId);
}

async function runVerification(query) {
  const panel = document.getElementById('verification-result-panel');
  if (!panel) return;

  panel.style.display = 'block';
  panel.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 20px;">Searching cryptographic credential registry...</div>';

  try {
    const res = await fetch(`/api/certificates/verify/${encodeURIComponent(query)}`);
    const json = await res.json();

    if (json.status === 'success' && json.verified && json.data) {
      const c = json.data;
      panel.innerHTML = `
        <div style="border-left: 4px solid var(--accent-emerald); padding-left: 18px;">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
            <div style="display: flex; align-items: center; gap: 8px;">
              <span class="badge badge-green" style="font-size: 0.85rem;">✓ OFFICIAL & VERIFIED AUTHENTIC</span>
              <span class="font-mono" style="color: var(--text-muted); font-size: 0.85rem;">${c.certificate_number}</span>
            </div>
            <button class="btn btn-gold btn-sm" onclick="viewCertificateByNumber('${c.certificate_number}')">View Certificate</button>
          </div>

          <h3 style="font-size: 1.4rem; color: #fff; margin-bottom: 4px;">Conferred to: ${c.trainee_name}</h3>
          <div style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 16px;">
            ${c.designation || 'Specialist'} • ${c.organization || 'Corporate Organization'}
          </div>

          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; background: rgba(15, 23, 42, 0.6); padding: 16px; border-radius: var(--radius-md); font-size: 0.85rem;">
            <div>
              <span style="color: var(--text-muted); display: block;">Programme Completed</span>
              <strong style="color: #fff;">${c.programme_title}</strong> (${c.programme_code})
            </div>
            <div>
              <span style="color: var(--text-muted); display: block;">Academic Standing</span>
              <strong style="color: var(--accent-amber);">${c.grade}</strong> (Final Score: ${c.score}%)
            </div>
            <div>
              <span style="color: var(--text-muted); display: block;">Conferral Date</span>
              <strong style="color: #fff;">${c.issue_date}</strong> (Valid until: ${c.expiry_date || 'Permanent'})
            </div>
            <div>
              <span style="color: var(--text-muted); display: block;">Instruction Lead</span>
              <strong style="color: #fff;">${c.instructor_name || 'Academic Directorate'}</strong>
            </div>
          </div>

          <div style="margin-top: 14px; padding-top: 10px; border-top: 1px solid var(--border-subtle); font-size: 0.75rem; color: var(--text-subtle);">
            <strong>SHA-256 Cryptographic Hash:</strong> <span class="font-mono">${c.verification_hash}</span>
          </div>
        </div>
      `;
    } else {
      panel.innerHTML = `
        <div style="border-left: 4px solid var(--accent-rose); padding-left: 18px;">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            <span class="badge badge-red">RECORD NOT FOUND</span>
          </div>
          <h4 style="color: #fff; margin-bottom: 6px;">No authentic certificate record was found for "${escapeHtml(query)}"</h4>
          <p style="color: var(--text-muted); font-size: 0.85rem;">
            Please ensure the Certificate ID or hash is typed accurately. Unverified credentials should be reported to the academic registry.
          </p>
        </div>
      `;
    }
  } catch (err) {
    panel.innerHTML = '<div style="color: var(--accent-rose); padding: 10px;">Verification server error. Please try again.</div>';
  }
}

// -----------------------------------------------------------------------------
// Forms Submission Handlers
// -----------------------------------------------------------------------------
function initForms() {
  // 1. Create Programme
  document.getElementById('form-create-programme')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
      title: document.getElementById('prog-title').value,
      category: document.getElementById('prog-category').value,
      level: document.getElementById('prog-level').value,
      instructor_id: document.getElementById('prog-instructor').value || null,
      duration_hours: document.getElementById('prog-hours').value,
      min_passing_score: document.getElementById('prog-pass-score').value,
      min_attendance_pct: document.getElementById('prog-att-pct').value,
      description: document.getElementById('prog-desc').value
    };

    try {
      const res = await fetch('/api/programmes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      const json = await res.json();
      if (json.status === 'success') {
        showToast('Training programme created successfully!');
        closeModal('modal-add-programme');
        e.target.reset();
        loadProgrammes();
        loadDashboard();
      } else {
        showToast(json.message || 'Error creating programme', 'error');
      }
    } catch (err) {
      showToast('Network error creating programme', 'error');
    }
  });

  // 2. Register Trainee
  document.getElementById('form-create-trainee')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
      full_name: document.getElementById('trainee-name').value,
      email: document.getElementById('trainee-email').value,
      phone: document.getElementById('trainee-phone').value,
      organization: document.getElementById('trainee-org').value,
      department_id: document.getElementById('trainee-dept').value || null
    };

    try {
      const res = await fetch('/api/trainees', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      const json = await res.json();
      if (json.status === 'success') {
        showToast('Trainee registered successfully!');
        closeModal('modal-add-trainee');
        e.target.reset();
        loadMetadata();
        loadDashboard();
      } else {
        showToast(json.message || 'Error registering trainee', 'error');
      }
    } catch (err) {
      showToast('Network error registering trainee', 'error');
    }
  });

  // 3. Enroll Trainee
  document.getElementById('form-enroll-trainee')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const trainee_id = document.getElementById('enroll-trainee-select').value;
    const programme_id = document.getElementById('enroll-prog-select').value;

    try {
      const res = await fetch('/api/enrollments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ trainee_id, programme_id })
      });
      const json = await res.json();
      if (json.status === 'success') {
        showToast('Trainee successfully enrolled in programme!');
        closeModal('modal-enroll-trainee');
        loadEnrollments();
        loadProgrammes();
        loadDashboard();
      } else {
        showToast(json.message || 'Error enrolling trainee', 'error');
      }
    } catch (err) {
      showToast('Network error enrolling trainee', 'error');
    }
  });

  // 4. Update Progress & Score
  document.getElementById('form-update-progress')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const eid = document.getElementById('edit-enrollment-id').value;
    const data = {
      progress_percentage: document.getElementById('edit-progress-pct').value,
      attendance_percentage: document.getElementById('edit-att-pct').value,
      assessment_score: document.getElementById('edit-score').value || null,
      remarks: document.getElementById('edit-remarks').value
    };

    try {
      const res = await fetch(`/api/enrollments/${eid}/progress`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      const json = await res.json();
      if (json.status === 'success') {
        showToast('Performance & progress updated!');
        closeModal('modal-update-progress');
        loadEnrollments();
        loadDashboard();
      } else {
        showToast(json.message || 'Error updating progress', 'error');
      }
    } catch (err) {
      showToast('Network error updating progress', 'error');
    }
  });

  // 5. Issue Certificate
  document.getElementById('form-issue-certificate')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const enrollment_id = document.getElementById('issue-enrollment-select').value;
    const template_style = document.getElementById('issue-template-select').value;
    const issued_by = document.getElementById('issue-authority-input').value;

    if (!enrollment_id) {
      showToast('Please select an eligible trainee.', 'error');
      return;
    }

    try {
      const res = await fetch('/api/certificates/issue', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enrollment_id, template_style, issued_by })
      });
      const json = await res.json();
      if (json.status === 'success') {
        showToast(`Certificate ${json.data.certificate_number} issued successfully!`);
        closeModal('modal-issue-cert');
        loadCertificates();
        loadEnrollments();
        loadDashboard();
        // Immediately view the newly issued certificate
        viewCertificateByNumber(json.data.certificate_number);
      } else {
        showToast(json.message || 'Failed to issue certificate', 'error');
      }
    } catch (err) {
      showToast('Network error issuing certificate', 'error');
    }
  });

  // 6. Verification Input Submit
  document.getElementById('btn-run-verification')?.addEventListener('click', () => {
    const q = document.getElementById('verify-input-query')?.value.trim();
    if (q) runVerification(q);
  });
  document.getElementById('verify-input-query')?.addEventListener('keyup', (e) => {
    if (e.key === 'Enter') {
      const q = e.target.value.trim();
      if (q) runVerification(q);
    }
  });

  // Filters Events
  document.getElementById('filter-prog-category')?.addEventListener('change', loadProgrammes);
  document.getElementById('filter-prog-status')?.addEventListener('change', loadProgrammes);
  document.getElementById('enrollment-status-filter')?.addEventListener('change', loadEnrollments);
  document.getElementById('trainee-filter-search')?.addEventListener('input', () => renderEnrollmentsTable(state.enrollments));
  document.getElementById('cert-status-filter')?.addEventListener('change', loadCertificates);
  document.getElementById('cert-filter-search')?.addEventListener('input', () => renderCertificatesTable(state.certificates));
}

function openUpdateProgressModal(id, name, course, prog, att, score, remarks) {
  document.getElementById('edit-enrollment-id').value = id;
  document.getElementById('edit-enrollment-trainee-name').textContent = name;
  document.getElementById('edit-enrollment-prog-title').textContent = course;
  document.getElementById('edit-progress-pct').value = prog;
  document.getElementById('edit-att-pct').value = att;
  document.getElementById('edit-score').value = score || '';
  document.getElementById('edit-remarks').value = remarks || '';
  openModal('modal-update-progress');
}

function openEnrollForProgramme(programmeId) {
  openModal('modal-enroll-trainee');
  const selProg = document.getElementById('enroll-prog-select');
  if (selProg) {
    selProg.innerHTML = state.programmes.map(p => `
      <option value="${p.programme_id}" ${p.programme_id === programmeId ? 'selected' : ''}>
        ${p.title} (${p.programme_code})
      </option>
    `).join('');
  }
}

function navigateToTraineesForProg(programmeId) {
  navigateToTab('trainees');
}

// -----------------------------------------------------------------------------
// MySQL DBMS Console & Database Switching
// -----------------------------------------------------------------------------
function initDbConsole() {
  // Test MySQL Connection in Modal
  document.getElementById('btn-test-mysql-conn')?.addEventListener('click', async () => {
    const feedback = document.getElementById('mysql-test-feedback');
    feedback.style.display = 'block';
    feedback.style.background = 'rgba(59, 130, 246, 0.15)';
    feedback.style.color = 'var(--primary)';
    feedback.textContent = 'Testing connection to MySQL server...';

    const config = {
      host: document.getElementById('mysql-host-input').value,
      port: document.getElementById('mysql-port-input').value,
      user: document.getElementById('mysql-user-input').value,
      password: document.getElementById('mysql-pass-input').value
    };

    try {
      const res = await fetch('/api/db/test-mysql', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      const json = await res.json();
      if (json.connected) {
        feedback.style.background = 'rgba(16, 185, 129, 0.2)';
        feedback.style.color = 'var(--accent-emerald)';
        feedback.textContent = '✓ ' + json.message;
      } else {
        feedback.style.background = 'rgba(244, 63, 94, 0.2)';
        feedback.style.color = 'var(--accent-rose)';
        feedback.textContent = '⚠ ' + json.message;
      }
    } catch (err) {
      feedback.style.background = 'rgba(244, 63, 94, 0.2)';
      feedback.style.color = 'var(--accent-rose)';
      feedback.textContent = 'Connection test failed: Network or server error.';
    }
  });

  // Connect & Migrate MySQL form submit
  document.getElementById('form-mysql-config')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const config = {
      host: document.getElementById('mysql-host-input').value,
      port: document.getElementById('mysql-port-input').value,
      user: document.getElementById('mysql-user-input').value,
      password: document.getElementById('mysql-pass-input').value,
      database: document.getElementById('mysql-dbname-input').value
    };

    try {
      const res = await fetch('/api/db/switch-mysql', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      const json = await res.json();
      if (json.status === 'success') {
        showToast(json.message);
        closeModal('modal-mysql-config');
        loadDbStatus();
        loadDashboard();
      } else {
        showToast(json.message || 'MySQL migration failed', 'error');
      }
    } catch (err) {
      showToast('Network error during MySQL migration', 'error');
    }
  });

  // Switch to SQLite button
  document.getElementById('btn-db-switch-sqlite')?.addEventListener('click', async () => {
    try {
      const res = await fetch('/api/db/switch-sqlite', { method: 'POST' });
      const json = await res.json();
      if (json.status === 'success') {
        showToast(json.message);
        loadDbStatus();
        loadDashboard();
      }
    } catch (err) {
      showToast('Failed to switch database mode.', 'error');
    }
  });

  document.getElementById('btn-db-tab-reconnect')?.addEventListener('click', () => {
    openModal('modal-mysql-config');
  });

  // Execute Raw SQL Query
  document.getElementById('btn-run-sql')?.addEventListener('click', async () => {
    const sql = document.getElementById('sql-console-input')?.value.trim();
    const resultsBox = document.getElementById('sql-results-container');
    if (!sql || !resultsBox) return;

    resultsBox.style.display = 'block';
    resultsBox.innerHTML = '<span style="color: var(--text-muted); font-size: 0.85rem;">Executing SQL...</span>';

    try {
      const res = await fetch('/api/db/execute-sql', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sql })
      });
      const json = await res.json();

      if (json.status === 'success' && json.data) {
        const d = json.data;
        if (d.columns && d.rows) {
          renderSqlTable(d.columns, d.rows, d.count, d.engine);
        } else {
          resultsBox.innerHTML = `
            <div style="color: var(--accent-emerald); font-size: 0.85rem;">
              ✓ Query executed successfully. Affected rows: <strong>${d.affected_rows || 0}</strong> [Engine: ${d.engine}]
            </div>
          `;
        }
      } else {
        resultsBox.innerHTML = `
          <div style="color: var(--accent-rose); font-size: 0.85rem;">
            ⚠ SQL Error: ${escapeHtml(json.message || 'Execution error')}
          </div>
        `;
      }
    } catch (err) {
      resultsBox.innerHTML = '<span style="color: var(--accent-rose); font-size: 0.85rem;">Network execution error.</span>';
    }
  });
}

function renderSqlTable(columns, rows, count, engine) {
  const resultsBox = document.getElementById('sql-results-container');
  if (!resultsBox) return;

  if (rows.length === 0) {
    resultsBox.innerHTML = `<div style="color: var(--text-muted); font-size: 0.85rem;">Empty result set (0 rows) [${engine}]</div>`;
    return;
  }

  const ths = columns.map(c => `<th>${escapeHtml(c)}</th>`).join('');
  const trs = rows.map(r => {
    const tds = columns.map(c => `<td>${escapeHtml(String(r[c] !== null && r[c] !== undefined ? r[c] : 'NULL'))}</td>`).join('');
    return `<tr>${tds}</tr>`;
  }).join('');

  resultsBox.innerHTML = `
    <div style="font-size: 0.78rem; color: var(--accent-cyan); margin-bottom: 8px;">
      Returned <strong>${count}</strong> record(s) on <strong>${engine.toUpperCase()}</strong> engine:
    </div>
    <table class="data-table font-mono" style="font-size: 0.8rem;">
      <thead><tr>${ths}</tr></thead>
      <tbody>${trs}</tbody>
    </table>
  `;
}

function setQueryPreset(sql) {
  const el = document.getElementById('sql-console-input');
  if (el) el.value = sql;
  document.getElementById('btn-run-sql')?.click();
}

async function loadDbStatus() {
  try {
    const res = await fetch('/api/db/status');
    const json = await res.json();
    if (json.status !== 'success') return;

    state.dbStatus = json.data;
    const d = json.data;

    // Badges & info in MySQL Console Tab
    const badge = document.getElementById('db-engine-active-badge');
    if (badge) {
      if (d.active_engine === 'mysql') {
        badge.className = 'badge badge-green';
        badge.textContent = 'MySQL 8.0 Live Engine';
      } else {
        badge.className = 'badge badge-amber';
        badge.textContent = 'SQLite Local Fallback Mode';
      }
    }

    const hostEl = document.getElementById('disp-db-host');
    const nameEl = document.getElementById('disp-db-name');
    const infoEl = document.getElementById('disp-db-info');
    if (hostEl) hostEl.textContent = `${d.mysql_config.host}:${d.mysql_config.port}`;
    if (nameEl) nameEl.textContent = d.mysql_config.database;
    if (infoEl) infoEl.textContent = d.mysql_info;

    // Render Table Counts
    renderTableCounts(d.table_stats || {});

    // Update Sidebar status pill
    updateDbPill(d.active_engine, d.mysql_config.host, d.mysql_config.database);
  } catch (err) {
    console.error('Failed to load db status:', err);
  }
}

function updateDbPill(engine, host, db) {
  const dot = document.getElementById('db-indicator-dot');
  const text = document.getElementById('db-indicator-text');
  if (!dot || !text) return;

  if (engine === 'mysql') {
    dot.className = 'dot-pulse online-mysql';
    text.textContent = 'MySQL Live';
    text.title = `Connected to ${host}/${db}`;
  } else {
    dot.className = 'dot-pulse sqlite-mode';
    text.textContent = 'SQLite Mode';
    text.title = 'Local DB mode active. Click to connect to MySQL';
  }
}

function renderTableCounts(stats) {
  const container = document.getElementById('table-counts-container');
  if (!container) return;

  const names = Object.keys(stats);
  if (names.length === 0) {
    container.innerHTML = '<span style="color: var(--text-muted);">No schema entities found.</span>';
    return;
  }

  container.innerHTML = names.map(t => `
    <div style="background: rgba(15, 23, 42, 0.6); padding: 10px 14px; border-radius: var(--radius-md); border: 1px solid var(--border-subtle); display: flex; justify-content: space-between; align-items: center;">
      <span class="font-mono" style="font-size: 0.82rem; color: #fff;">${t}</span>
      <span class="badge badge-blue font-mono">${stats[t]} rows</span>
    </div>
  `).join('');
}

// -----------------------------------------------------------------------------
// Global Search
// -----------------------------------------------------------------------------
function initGlobalSearch() {
  const input = document.getElementById('global-search-input');
  if (!input) return;

  input.addEventListener('keyup', (e) => {
    const q = e.target.value.toLowerCase().trim();
    if (!q) return;

    if (e.key === 'Enter') {
      // Determine best tab to switch to or filter
      if (q.startsWith('cert')) {
        navigateToTab('certificates');
        const cSearch = document.getElementById('cert-filter-search');
        if (cSearch) { cSearch.value = q; renderCertificatesTable(state.certificates); }
      } else {
        navigateToTab('programmes');
        const filtered = state.programmes.filter(p => 
          p.title.toLowerCase().includes(q) || 
          p.programme_code.toLowerCase().includes(q) ||
          p.category.toLowerCase().includes(q)
        );
        renderProgrammesGrid(filtered);
      }
    }
  });
}

// -----------------------------------------------------------------------------
// Utility Functions
// -----------------------------------------------------------------------------
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function escapeQuote(str) {
  if (!str) return '';
  return String(str).replace(/'/g, "\\'");
}
