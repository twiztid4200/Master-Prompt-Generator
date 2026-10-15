// MASTER AWAKENING Command Center Dashboard
// Local-first. No network except same-origin static fetches. No secrets. No execution.

const STORAGE_KEY = 'master-awakening-dashboard-v1';
const KNOWN_RUNS = [
  '../factory/runs/20261009T175639Z-46b3c212.json',
  '../factory/runs/20261011T091754Z-7159f51a.json'
];

let state = null;

async function loadBaseline() {
  try {
    const res = await fetch('data/baseline.json');
    if (!res.ok) throw new Error('baseline fetch failed');
    return await res.json();
  } catch (e) {
    console.error('Failed to load baseline', e);
    return {
      meta: { label: 'FAILED TO LOAD BASELINE' },
      projects: [],
      tasks: [],
      milestones: [],
      budget: { known_revenue: 'UNKNOWN', known_expenses: 'UNKNOWN' },
      knowledge: [],
      karma_arkade: { prototypes: [], notes: 'Data unavailable' }
    };
  }
}

function loadState() {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved) {
    try {
      return JSON.parse(saved);
    } catch (e) {
      console.warn('Malformed localStorage, ignoring');
    }
  }
  return null;
}

function saveState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function resetState() {
  if (confirm('Reset all local edits to baseline? This cannot be undone.')) {
    localStorage.removeItem(STORAGE_KEY);
    location.reload();
  }
}

function statusClass(s) {
  const map = {
    planned: 'planned',
    'in-progress': 'in-progress',
    blocked: 'blocked',
    complete: 'complete',
    verified: 'verified',
    UNKNOWN: 'unknown',
    'NEEDS VERIFICATION': 'unknown'
  };
  return map[s] || 'planned';
}

function renderOverview() {
  const el = document.getElementById('overview');
  const priority = state.projects.find(p => p.priority === 'high') || state.projects[0];
  const blocked = state.tasks.filter(t => t.status === 'blocked');
  const recent = state.milestones.filter(m => m.status === 'verified').slice(-3);

  el.innerHTML = `
    <div class="card">
      <h2>Current Priority</h2>
      <p><strong>${priority?.name || 'UNKNOWN'}</strong> — ${priority?.next_actions?.join(', ') || 'NEEDS VERIFICATION'}</p>
      <span class="status ${statusClass(priority?.status)}">${priority?.status || 'unknown'}</span>
    </div>
    <div class="grid grid-2">
      <div class="card">
        <h3>Project Health</h3>
        ${state.projects.map(p => `<div>${p.name}: <span class="status ${statusClass(p.health)}">${p.health}</span></div>`).join('')}
      </div>
      <div class="card">
        <h3>Blocked Tasks</h3>
        ${blocked.length ? blocked.map(t => `<div class="task blocked">${t.title}</div>`).join('') : '<div class="empty">None recorded</div>'}
      </div>
    </div>
    <div class="card">
      <h3>Recent Verified Milestones</h3>
      ${recent.length ? recent.map(m => `<div>${m.title} <span class="status verified">verified</span> — ${m.evidence}</div>`).join('') : '<div class="empty">No verified milestones in baseline</div>'}
    </div>
    <div class="card">
      <h3>Next Actions</h3>
      <ul>${state.projects.flatMap(p => p.next_actions || []).map(a => `<li>${a}</li>`).join('') || '<li>NEEDS VERIFICATION</li>'}</ul>
    </div>
  `;
}

function renderRoadmap() {
  const el = document.getElementById('roadmap');
  el.innerHTML = `
    <div class="card">
      <h2>Tasks</h2>
      <button onclick="showTaskForm()">Add Task</button>
      <button onclick="resetState()">Reset local edits</button>
      ${state.tasks.map(t => `
        <div class="task ${t.status}">
          <strong>${t.title}</strong> <span class="status ${statusClass(t.status)}">${t.status}</span>
          <div>Project: ${t.project} | Verification: ${t.verification_status || 'none'}</div>
          <div>Evidence: ${t.evidence_ref || 'none'} | Updated: ${t.last_updated || 'UNKNOWN'}</div>
          <div>Acceptance: ${(t.acceptance_criteria || []).join('; ')}</div>
          <button onclick="editTask('${t.id}')">Edit</button>
        </div>
      `).join('') || '<div class="empty">No tasks</div>'}
    </div>
    <div class="card">
      <h2>Milestones</h2>
      ${state.milestones.map(m => `<div>${m.title} <span class="status ${statusClass(m.status)}">${m.status}</span> (${m.progress})</div>`).join('')}
    </div>
  `;
}

function renderAgentOps() {
  const el = document.getElementById('agent-ops');
  el.innerHTML = '<div class="card"><h2>Mission Runs (read-only)</h2><div id="runs-container">Loading logs...</div></div>';
  loadRuns();
}

async function loadRuns() {
  const container = document.getElementById('runs-container');
  let html = '';
  for (const path of KNOWN_RUNS) {
    try {
      const res = await fetch(path);
      if (!res.ok) throw new Error(res.status);
      const run = await res.json();
      const isMock = run.live === false || run.usage?.provider === 'mock';
      html += `
        <div class="card">
          <h3>${run.id || path}</h3>
          <span class="badge ${isMock ? 'mock' : 'live'}">${isMock ? 'MOCK' : 'LIVE'}</span>
          <p><strong>Goal:</strong> ${run.goal}</p>
          <p>Result: <span class="status ${run.result === 'PASS' ? 'verified' : 'blocked'}">${run.result}</span>
             Duration: ${run.elapsed_ms} ms | Retries: ${run.retry_count ?? 0}</p>
          <p>Provider: ${run.usage?.provider || 'UNKNOWN'} | Cost: ${run.estimated_cost ?? run.usage?.estimated_cost_usd ?? 'null'}</p>
          <p>Verification: ${run.verdict?.verdict || 'UNKNOWN'}</p>
          <details><summary>Raw log (truncated)</summary><pre class="log">${JSON.stringify(run, null, 2).slice(0, 2000)}...</pre></details>
        </div>
      `;
    } catch (e) {
      html += `<div class="empty">Failed to load ${path}: ${e.message}</div>`;
    }
  }
  container.innerHTML = html || '<div class="empty">No runs available</div>';
}

function renderIncome() {
  const el = document.getElementById('income');
  const b = state.budget || {};
  el.innerHTML = `
    <div class="card">
      <h2>Income & Resources</h2>
      <p>Known revenue: <strong>${b.known_revenue || 'UNKNOWN'}</strong></p>
      <p>Known expenses: <strong>${b.known_expenses || 'UNKNOWN'}</strong></p>
      <p>DevKit readiness: NEEDS VERIFICATION</p>
      <p class="empty">${b.notes || 'No financial records in baseline. Do not invent figures.'}</p>
    </div>
  `;
}

function renderKnowledge() {
  const el = document.getElementById('knowledge');
  el.innerHTML = `
    <div class="card">
      <h2>Knowledge & Research</h2>
      ${state.knowledge.map(k => `
        <div class="task">
          <strong>${k.title}</strong> (${k.type})
          <div>Source: ${k.source}</div>
          <div>${k.summary}</div>
        </div>
      `).join('') || '<div class="empty">No entries</div>'}
      <p class="empty">Obsidian-compatible notes live under factory/memory/. This view is a summary only.</p>
    </div>
  `;
}

function renderKarma() {
  const el = document.getElementById('karma');
  const k = state.karma_arkade || {};
  el.innerHTML = `
    <div class="card">
      <h2>Karma ArKade</h2>
      <p>Prototype milestones: ${k.prototypes?.length ? k.prototypes.join(', ') : 'NONE recorded'}</p>
      <p>Gameplay features: ${k.features?.length ? k.features.join(', ') : 'NONE'}</p>
      <p>Phone testing: ${k.phone_testing || 'UNKNOWN'}</p>
      <p>Bugs: ${k.bugs?.length ? k.bugs.join(', ') : 'NONE recorded'}</p>
      <div class="empty">${k.notes || 'No prototype data in current repository. NEEDS VERIFICATION'}</div>
    </div>
  `;
}

function showSection(id) {
  document.querySelectorAll('section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  document.querySelector(`nav button[data-section="${id}"]`).classList.add('active');
  if (id === 'overview') renderOverview();
  if (id === 'roadmap') renderRoadmap();
  if (id === 'agent-ops') renderAgentOps();
  if (id === 'income') renderIncome();
  if (id === 'knowledge') renderKnowledge();
  if (id === 'karma') renderKarma();
}

function showTaskForm(task) {
  const form = document.getElementById('task-form');
  form.style.display = 'block';
  document.getElementById('task-id').value = task?.id || '';
  document.getElementById('task-title').value = task?.title || '';
  document.getElementById('task-project').value = task?.project || 'factory';
  document.getElementById('task-status').value = task?.status || 'planned';
  document.getElementById('task-evidence').value = task?.evidence_ref || '';
  document.getElementById('task-notes').value = task?.notes || '';
}

function editTask(id) {
  const task = state.tasks.find(t => t.id === id);
  if (task) showTaskForm(task);
}

function saveTask(ev) {
  ev.preventDefault();
  const id = document.getElementById('task-id').value || 't' + Date.now();
  const task = {
    id,
    title: document.getElementById('task-title').value,
    project: document.getElementById('task-project').value,
    status: document.getElementById('task-status').value,
    evidence_ref: document.getElementById('task-evidence').value || null,
    verification_status: document.getElementById('task-status').value === 'verified' ? 'verified' : 'none',
    last_updated: new Date().toISOString().slice(0, 10),
    notes: document.getElementById('task-notes').value,
    acceptance_criteria: [],
    dependencies: []
  };
  const idx = state.tasks.findIndex(t => t.id === id);
  if (idx >= 0) state.tasks[idx] = { ...state.tasks[idx], ...task };
  else state.tasks.push(task);
  saveState();
  document.getElementById('task-form').style.display = 'none';
  renderRoadmap();
}

async function init() {
  const baseline = await loadBaseline();
  const saved = loadState();
  state = saved || baseline;
  // Ensure structure
  state.tasks = state.tasks || [];
  state.projects = state.projects || [];
  state.milestones = state.milestones || [];
  state.knowledge = state.knowledge || [];
  state.budget = state.budget || {};
  state.karma_arkade = state.karma_arkade || {};

  document.getElementById('task-form').addEventListener('submit', saveTask);
  document.getElementById('cancel-task').addEventListener('click', () => {
    document.getElementById('task-form').style.display = 'none';
  });

  showSection('overview');
}

init();
