const API_URL = "https://student-idea-hub.onrender.com";

// --- GLOBAL STATE ---
let currentUser = JSON.parse(localStorage.getItem("user"));
let currentProjectId = null;

// --- UTILS ---
function showToast(msg, type = 'success') {
    const t = document.createElement('div');
    t.className = `toast ${type} active`;
    t.innerText = msg;
    document.body.appendChild(t);
    setTimeout(() => { t.remove(); }, 3000);
}

function openModal(id) {
    document.getElementById(id).style.display = 'flex';
    setTimeout(() => document.getElementById(id).classList.add('active'), 10);
}

function closeModal(id) {
    document.getElementById(id).classList.remove('active');
    setTimeout(() => document.getElementById(id).style.display = 'none', 200);
}

function logout() {
    localStorage.removeItem("user");
    window.location.href = "index.html";
}

// --- LANDING & AUTH ---
async function handleLogin(email, password) {
    try {
        const res = await fetch(`${API_URL}/auth/login`, {
            method: 'POST', body: JSON.stringify({ email, password }),
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        if (res.ok) {
            localStorage.setItem("user", JSON.stringify(data.user));
            window.location.href = "main.html";
        } else alert(data.detail || "Login Failed");
    } catch (e) { alert("Network Error"); }
}

async function handleSignup(fullName, email, password, role = "Student", skills = "", bio = "", portfolio = "", phone = "") {
    try {
        const skillsArr = skills.split(',').map(s => s.trim()).filter(s => s);
        const portfolioArr = portfolio ? [portfolio] : [];

        const res = await fetch(`${API_URL}/auth/signup`, {
            method: 'POST',
            body: JSON.stringify({
                full_name: fullName,
                email,
                password,
                role,
                skills: skillsArr,
                bio,
                portfolio_links: portfolioArr,
                phone_number: phone,
                avatar_url: `https://ui-avatars.com/api/?name=${fullName}`
            }),
            headers: { 'Content-Type': 'application/json' }
        });
        if (res.ok) { alert("Success! Login now."); window.location.reload(); }
        else {
            const err = await res.json();
            alert("Signup Failed: " + (err.detail || "Unknown error"));
        }
    } catch (e) { alert("Network Error"); console.error(e); }
}

// --- MAIN HUB ---
async function loadFeed(filter = 'all') {
    const grid = document.getElementById('feedGrid');
    if (!grid) return;
    grid.innerHTML = '<div style="padding:20px;">Loading...</div>';

    let url = `${API_URL}/projects`;
    if (filter === 'my' && currentUser) url += `?mine=true&user_id=${currentUser.id}`;

    const res = await fetch(url);
    const projects = await res.json();

    if (projects.length === 0) {
        grid.innerHTML = '<div style="grid-column:1/-1; text-align:center; color:#777;">No projects yet.</div>';
        return;
    }

    grid.innerHTML = projects.map(p => `
        <div class="project-card" onclick="window.location.href='project_detail.html?id=${p.id}'">
            <div class="card-header">
                <span class="card-title">${p.title}</span>
                <span class="badge ${p.stage === 'Idea' ? 'badge-idea' : 'badge-mvp'}">${p.stage}</span>
            </div>
            <div class="tech-stack">${p.tags.map(t => `<span class="badge badge-tag">${t}</span>`).join('')}</div>
            <p class="card-desc">${p.description}</p>
            <div class="card-footer">
                <span style="font-size:0.9rem;">${p.owner_name}</span>
            </div>
        </div>
    `).join('');
}

async function handlePostProject(e) {
    e.preventDefault();
    if (!currentUser) return alert("Login first");

    const tags = document.getElementById('pTags').value.split(',').map(s => s.trim());
    const roles = document.getElementById('pRoles').value.split(',').map(s => s.trim());

    const data = {
        owner_id: currentUser.id,
        title: document.getElementById('pTitle').value,
        description: document.getElementById('pDesc').value,
        domain: document.getElementById('pDomain').value,
        difficulty: document.getElementById('pDifficulty').value,
        tags: tags, required_roles: roles, stage: "Idea"
    };

    const res = await fetch(`${API_URL}/projects`, {
        method: 'POST', body: JSON.stringify(data),
        headers: { 'Content-Type': 'application/json' }
    });
    if (res.ok) { showToast("Posted!"); closeModal('postProjectModal'); loadFeed(); }
}

// --- PROJECT DETAIL ---
async function loadProjectDetail() {
    const params = new URLSearchParams(window.location.search);
    currentProjectId = params.get('id');
    if (!currentProjectId) return;

    const res = await fetch(`${API_URL}/projects/${currentProjectId}`);
    if (!res.ok) return document.getElementById('projectLoading').innerText = "Project not found";

    const data = await res.json();
    const p = data.project;

    document.getElementById('projectContainer').style.display = 'block';
    document.getElementById('projectLoading').style.display = 'none';

    // Fill Info
    document.getElementById('dtTitle').innerText = p.title;
    document.getElementById('dtDesc').innerText = p.description;
    document.getElementById('dtStage').innerText = p.stage;
    document.getElementById('dtStage').className = `badge ${p.stage === 'Idea' ? 'badge-idea' : 'badge-mvp'}`;
    document.getElementById('dtDomain').innerText = p.domain;
    document.getElementById('dtOwner').innerText = "By " + p.owner_name;
    document.getElementById('dtTags').innerHTML = p.tags.map(t => `<span class="badge badge-tag">${t}</span>`).join('');

    // Fill Roles (Overview)
    const rolesDiv = document.getElementById('dtRoles');
    rolesDiv.innerHTML = p.required_roles.map(r => `<span class="badge" style="background:#333;">${r}</span>`).join('');

    // Populate Apply Modal Roles
    const appRoleSelect = document.getElementById('appRole');
    appRoleSelect.innerHTML = p.required_roles.map(r => `<option>${r}</option>`).join('');

    // Render Team
    const teamDiv = document.getElementById('teamList');
    teamDiv.innerHTML = data.members.map(m => `
        <div class="project-card" style="padding:15px; display:flex; align-items:center; gap:10px;">
            <div class="avatar"></div>
            <div>
                <strong>${m.full_name}</strong><br>
                <small style="color:#aaa">${m.role}</small>
            </div>
        </div>
    `).join('');

    // Render Tasks
    renderKanban(data.tasks);

    // Conditional Owner Buttons
    if (currentUser && currentUser.id === p.owner_id) {
        document.getElementById('btnAction').style.display = 'none'; // Hide apply loop
        document.getElementById('btnEdit').style.display = 'inline-flex';
        document.getElementById('btnDelete').style.display = 'inline-flex';

        // Populate owner apps
        document.getElementById('ownerAppsSection').style.display = 'block';
        loadAppsList(currentProjectId);

        // Store data for edit modal
        document.getElementById('eTitle').value = p.title;
        document.getElementById('eDesc').value = p.description;
        document.getElementById('eDomain').value = p.domain;
        document.getElementById('eStage').value = p.stage;
        document.getElementById('eRepo').value = p.repo_link || '';
    } else {
        // Only show apply if not owner and not member (todo check membership)
        document.getElementById('btnAction').style.display = 'inline-flex';
        document.getElementById('btnMsgOwner').style.display = 'inline-flex';
        document.getElementById('btnMsgOwner').onclick = () => window.location.href = `messages.html?user=${p.owner_id}`;
    }
}

function renderKanban(tasks) {
    const cols = { 'To Do': 'list-todo', 'In Progress': 'list-progress', 'Done': 'list-done' };
    const counts = { 'To Do': 0, 'In Progress': 0, 'Done': 0 };

    // Clear lists
    Object.values(cols).forEach(id => document.getElementById(id).innerHTML = '');

    tasks.forEach(t => {
        if (counts[t.status] !== undefined) counts[t.status]++;
        const el = document.getElementById(cols[t.status] || 'list-todo');
        el.innerHTML += `
            <div class="task-card">
                <strong>${t.title}</strong><br>
                <small style="color:#777;">${t.priority}</small>
                <div style="margin-top:5px; font-size:0.8rem;">
                    ${t.status !== 'Done' ? `<span onclick="updateTask(${t.id}, 'Done')" style="color:var(--success); cursor:pointer;">Mark Done</span>` : ''}
                </div>
            </div>
        `;
    });

    // Update counts
    document.getElementById('count-todo').innerText = counts['To Do'];
    document.getElementById('count-progress').innerText = counts['In Progress'];
    document.getElementById('count-done').innerText = counts['Done'];
}

async function addTask() {
    const title = document.getElementById('tTitle').value;
    const status = document.getElementById('tStatus').value;

    await fetch(`${API_URL}/tasks`, {
        method: 'POST', body: JSON.stringify({ project_id: currentProjectId, title, status }),
        headers: { 'Content-Type': 'application/json' }
    });
    closeModal('taskModal');
    loadProjectDetail(); // Refresh
}

async function updateAppStatus(appId, status) {
    // 1. Update Status
    const res = await fetch(`${API_URL}/applications/${appId}/status?status=${status}`, { method: 'PUT' });

    if (res.ok && status === 'Accepted') {
        // 2. If Accepted, send Welcome Message automatically
        try {
            // We need the applicant ID. Since we don't have it handy in args, let's fetch the app details first or 
            // since we are in the context of the list, we can find it in the DOM or re-fetch.
            // A cleaner way for this quick fix: Fetch the specific application to get details.
            // For now, let's just trigger a reload which is safe, AND send the message if we can get the ID.

            // To do this robustly without extra fetches, let's look at the `loadOwnerApps` data. 
            // But to be safe and simple:
            // We can't easily get the applicant ID here without passing it. 
            // Let's modify the HTML generation in loadOwnerApps to pass the applicant ID to this function.
        } catch (e) { console.error("Auto-message failed", e); }

        showToast("Application Accepted! Member added.");
    }

    loadOwnerApps(currentProjectId);
    loadProjectDetail(); // Refresh members
}

// Updated to accept applicantId for messaging
async function updateAppStatusWithMsg(appId, status, applicantId, applicantName) {
    const res = await fetch(`${API_URL}/applications/${appId}/status?status=${status}`, { method: 'PUT' });

    if (res.ok && status === 'Accepted') {
        // Automated Message
        const msg = `Congratulations ${applicantName}! Your application has been accepted. Welcome to the team! Let's start building.`;
        await fetch(`${API_URL}/messages?user_id=${currentUser.id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ receiver_id: applicantId, message: msg })
        });
        showToast(`Accepted & Message sent to ${applicantName}`);
    }

    loadOwnerApps(currentProjectId);
    loadProjectDetail();
}

async function submitApplication() {
    const role = document.getElementById('appRole').value;
    const msg = document.getElementById('appMsg').value;

    const res = await fetch(`${API_URL}/applications`, {
        method: 'POST', body: JSON.stringify({
            project_id: currentProjectId,
            applicant_id: currentUser.id,
            role_applied_for: role,
            message: msg
        }),
        headers: { 'Content-Type': 'application/json' }
    });

    if (res.ok) { showToast("Applied!"); closeModal('applyModal'); }
    else alert("Failed to apply");
}

function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    event.target.classList.add('active');
    document.getElementById(`tab-${tabName}`).classList.add('active');
    if (tabName === 'chat') loadChat();
}

// --- INIT ---
window.onload = function () {
    if (document.getElementById('feedGrid')) {
        if (!currentUser) window.location.href = 'index.html';
        document.getElementById('userNameDisplay').innerText = currentUser?.full_name;
        loadFeed();
    }
    if (document.getElementById('projectContainer')) {
        loadProjectDetail();
    }
};

// --- CHAT ---
async function loadChat() {
    if (!currentProjectId) return;
    const res = await fetch(`${API_URL}/projects/${currentProjectId}/chat`);
    if (res.ok) {
        const msgs = await res.json();
        const chatDiv = document.getElementById('chatMessages');
        if (msgs.length === 0) {
            chatDiv.innerHTML = '<div style="text-align:center; color:#555; margin-top:50px;">Start the conversation...</div>';
            return;
        }
        chatDiv.innerHTML = msgs.map(m => `
            <div style="margin-bottom:10px; display:flex; gap:10px;">
                <div class="avatar" style="width:30px; height:30px; font-size:12px;"></div>
                <div>
                    <div style="font-size:0.8rem; color:var(--primary); font-weight:bold;">${m.sender_name}</div>
                    <div style="background:#333; padding:8px 12px; border-radius:0 12px 12px 12px; font-size:0.9rem;">${m.message}</div>
                    <div style="font-size:0.7rem; color:#666;">${new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                </div>
            </div>
        `).join('');
        chatDiv.scrollTop = chatDiv.scrollHeight;
    }
}

async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const msg = input.value.trim();
    if (!msg || !currentUser) return;

    await fetch(`${API_URL}/projects/${currentProjectId}/chat`, {
        method: 'POST', body: JSON.stringify({ project_id: currentProjectId, sender_id: currentUser.id, message: msg }),
        headers: { 'Content-Type': 'application/json' }
    });
    input.value = '';
    loadChat();
}

// --- OWNER APPS ---
async function loadOwnerApps(projectId) {
    // Check if owner
    const pOwnerId = document.getElementById('btnAction').getAttribute('data-owner-id'); // Need to store this
    if (!currentUser || (pOwnerId && parseInt(pOwnerId) !== currentUser.id)) return;

    document.getElementById('ownerAppsSection').style.display = 'block';

    const res = await fetch(`${API_URL}/projects/${projectId}/applications`);
    const apps = await res.json();

    const list = document.getElementById('appList');
    if (apps.length === 0) {
        list.innerHTML = '<div style="color:#777;">No pending applications.</div>';
        return;
    }

    list.innerHTML = apps.map(a => `
        <div class="project-card" style="padding:15px; border-left: 4px solid ${a.status === 'Pending' ? 'var(--secondary)' : (a.status === 'Accepted' ? 'var(--success)' : 'var(--danger)')}">
            <div style="display:flex; justify-content:space-between; align-items:start;">
                <div>
                    <strong>${a.full_name}</strong> applied for <strong>${a.role_applied_for}</strong>
                    <p style="font-size:0.9rem; color:#ccc; margin:5px 0;">"${a.message}"</p>
                    <small style="color:#777;">Skills: ${(a.skills || []).join(', ')}</small>
                </div>
                ${a.status === 'Pending' ? `
                <div style="display:flex; gap:5px;">
                    <button class="btn btn-primary btn-sm" onclick="updateAppStatusWithMsg(${a.id}, 'Accepted', ${a.applicant_id}, '${a.full_name}')">Accept</button>
                    <button class="btn btn-secondary btn-sm" style="background:#444;" onclick="updateAppStatus(${a.id}, 'Rejected')">Reject</button>
                    <button class="btn btn-secondary btn-sm" style="background:#333; color:var(--primary);" onclick="window.location.href='messages.html?user=${a.applicant_id}'"><i class="fas fa-comment"></i> Message</button>
                </div>` : `<span class="badge" style="background:#333;">${a.status}</span>`}
            </div>
        </div>
    `).join('');
}

// --- EDIT & DELETE PROJECT ---
function openEditModal() {
    openModal('editModal');
}

async function submitEditProject() {
    if (!currentUser || !currentProjectId) return;

    // We reuse values from detail page load for roles/tags for now to avoid complexity in this modal
    // Ideally the modal should have full tag/role editing
    // For MVP, we update: Title, Desc, Domain, Stage, Repo

    const data = {
        owner_id: currentUser.id,
        title: document.getElementById('eTitle').value,
        description: document.getElementById('eDesc').value,
        domain: document.getElementById('eDomain').value,
        stage: document.getElementById('eStage').value,
        repo_link: document.getElementById('eRepo').value,
        // Keeping existing tags/roles
        // In a real app we'd fetch these from the current state properly
        tags: [],
        required_roles: [],
        difficulty: "Medium" // default
    };

    // Fetch current project to preserve tags/roles
    // Optimized: we should have stored this in a variable. 
    // Let's do a quick fetch to be safe or use what's on screen if we parse it back.
    // Simpler: Just Fetch
    const resGet = await fetch(`${API_URL}/projects/${currentProjectId}`);
    const pData = await resGet.json();
    data.tags = pData.project.tags;
    data.required_roles = pData.project.required_roles;
    data.difficulty = pData.project.difficulty;

    const res = await fetch(`${API_URL}/projects/${currentProjectId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    if (res.ok) {
        showToast('Project Updated!');
        closeModal('editModal');
        loadProjectDetail();
    } else {
        alert('Failed to update');
    }
}

async function deleteProject() {
    if (!confirm("Are you sure you want to delete this project? This cannot be undone.")) return;

    const res = await fetch(`${API_URL}/projects/${currentProjectId}?user_id=${currentUser.id}`, {
        method: 'DELETE'
    });

    if (res.ok) {
        alert("Project deleted.");
        window.location.href = "main.html";
    } else {
        alert("Delete failed.");
    }
}

async function loadAppsList(pid) {
    loadOwnerApps(pid); // Reusing existing function name but ensuring it passes ID
}
