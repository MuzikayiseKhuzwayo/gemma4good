// AOS Studio Cockpit Interactive Controller
document.addEventListener('DOMContentLoaded', () => {
    // Tab Navigation
    const navItems = document.querySelectorAll('.nav-item');
    const tabPanes = document.querySelectorAll('.tab-pane');

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetTab = item.getAttribute('data-tab');
            navItems.forEach(i => i.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));

            item.classList.add('active');
            const pane = document.getElementById(targetTab);
            if (pane) pane.classList.add('active');

            // Trigger data refresh depending on tab
            if (targetTab === 'tab-knowledge') {
                loadIndexedFiles();
                loadGraphSnapshot();
            } else if (targetTab === 'tab-security') {
                loadSecurityAudits();
                loadPendingApprovals();
            } else if (targetTab === 'tab-telemetry') {
                loadTelemetry();
                loadSwarmStatus();
            }
        });
    });

    // View Toggle (Cockpit Studio vs Mobile Simulator)
    const btnToggleView = document.getElementById('btn-toggle-view');
    const cockpitContainer = document.querySelector('.cockpit-container');
    const phoneContainer = document.getElementById('phone-container');

    if (btnToggleView) {
        btnToggleView.addEventListener('click', () => {
            if (phoneContainer.style.display === 'none') {
                cockpitContainer.style.display = 'none';
                phoneContainer.style.display = 'block';
                document.body.classList.remove('mode-cockpit');
                btnToggleView.querySelector('span').innerText = 'Toggle Studio';
            } else {
                phoneContainer.style.display = 'none';
                cockpitContainer.style.display = 'flex';
                document.body.classList.add('mode-cockpit');
                btnToggleView.querySelector('span').innerText = 'Toggle Mobile';
            }
        });
    }

    // Phone simulator view switching
    const viewHome = document.getElementById('view-home');
    const viewIntent = document.getElementById('view-intent');
    const phoneCloseBtn = document.getElementById('phone-close-btn');

    if (viewHome && viewIntent) {
        viewHome.addEventListener('click', () => {
            viewHome.classList.remove('active');
            viewIntent.classList.add('active');
        });
    }
    if (phoneCloseBtn && viewHome && viewIntent) {
        phoneCloseBtn.addEventListener('click', () => {
            viewIntent.classList.remove('active');
            viewHome.classList.add('active');
        });
    }

    // Elements
    const feed = document.getElementById('feed');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const micBtn = document.getElementById('mic-btn');
    const clearFeedBtn = document.getElementById('clear-feed-btn');
    const halLog = document.getElementById('hal-log');
    const pendingBadge = document.getElementById('pending-badge');

    // ---------------- INTENT & FEED HANDLING ----------------
    function addMessage(text, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user' : 'system'}`;

        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'bubble';

        const textP = document.createElement('p');
        textP.innerText = text;

        bubbleDiv.appendChild(textP);
        messageDiv.appendChild(bubbleDiv);

        feed.appendChild(messageDiv);
        feed.scrollTop = feed.scrollHeight;

        // Also duplicate into phone feed if present
        const phoneFeed = document.getElementById('phone-feed');
        if (phoneFeed) {
            const clone = messageDiv.cloneNode(true);
            phoneFeed.appendChild(clone);
            phoneFeed.scrollTop = phoneFeed.scrollHeight;
        }
    }

    function addHalLog(type, text) {
        if (!halLog) return;
        const entry = document.createElement('div');
        entry.className = 'log-entry';
        entry.innerHTML = `<span class="log-tag">[${type}]</span> ${text}`;
        halLog.prepend(entry);
        while (halLog.children.length > 20) {
            halLog.removeChild(halLog.lastChild);
        }
    }

    async function dispatchIntent(intentText) {
        if (!intentText.trim()) return;
        addMessage(intentText, true);
        if (userInput) userInput.value = '';

        // Add temporary reasoning indicator
        const thinkingDiv = document.createElement('div');
        thinkingDiv.className = 'message system thinking-msg';
        thinkingDiv.innerHTML = `<div class="bubble"><p><em>⚡ Latent Kernel Reasoning & Dual Routing...</em></p></div>`;
        feed.appendChild(thinkingDiv);
        feed.scrollTop = feed.scrollHeight;

        try {
            const res = await fetch('/api/intent', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ intent: intentText })
            });
            const data = await res.json();
            if (feed.contains(thinkingDiv)) feed.removeChild(thinkingDiv);

            if (data.responses) {
                data.responses.forEach(r => {
                    addMessage(r, false);
                    if (r.length < 100 && !r.includes('[')) {
                        speakText(r);
                    }
                });
            }

            if (data.widgets) {
                data.widgets.forEach(w => renderWidget(w));
            }

            // Refresh stats & pending approvals after intent dispatch
            loadTelemetry();
            loadPendingApprovals();
        } catch (err) {
            if (feed.contains(thinkingDiv)) feed.removeChild(thinkingDiv);
            addMessage(`[AOS Error] Connection failed: ${err.message}`, false);
        }
    }

    if (sendBtn && userInput) {
        sendBtn.addEventListener('click', () => dispatchIntent(userInput.value));
        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') dispatchIntent(userInput.value);
        });
    }

    // Phone send button
    const phoneSendBtn = document.getElementById('phone-send-btn');
    const phoneUserInput = document.getElementById('phone-user-input');
    if (phoneSendBtn && phoneUserInput) {
        phoneSendBtn.addEventListener('click', () => dispatchIntent(phoneUserInput.value));
        phoneUserInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') dispatchIntent(phoneUserInput.value);
        });
    }

    // Quick Prompt Chips
    document.querySelectorAll('.chip-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const intent = btn.getAttribute('data-intent');
            if (userInput) userInput.value = intent;
            dispatchIntent(intent);
        });
    });

    // Clear Feed
    if (clearFeedBtn) {
        clearFeedBtn.addEventListener('click', async () => {
            try {
                await fetch('/api/new_chat', { method: 'POST' });
                feed.innerHTML = `
                    <div class="message system">
                        <div class="bubble">
                            <p>✨ Session cleared. Latent Kernel ready for new operations.</p>
                        </div>
                    </div>
                `;
                loadTelemetry();
            } catch (e) {
                console.error('Failed to clear session:', e);
            }
        });
    }

    // ---------------- DYNAMIC DSL WIDGET RENDERING ----------------
    function renderWidget(widget) {
        const container = document.createElement('div');
        container.className = 'canvas-widget';

        if (widget.widget === 'TABLE') {
            let html = `<div class="widget-title">📊 ${widget.title || 'Data View'}</div><table class="widget-table"><thead><tr>`;
            (widget.columns || []).forEach(col => { html += `<th>${col}</th>`; });
            html += `</tr></thead><tbody>`;
            (widget.rows || []).forEach(row => {
                html += `<tr>`;
                row.forEach(cell => { html += `<td>${cell}</td>`; });
                html += `</tr>`;
            });
            html += `</tbody></table>`;
            container.innerHTML = html;

        } else if (widget.widget === 'APPROVAL_CARD') {
            container.className += ' approval-card';
            container.innerHTML = `
                <div class="widget-title" style="color: var(--warning);">🛡️ Operator Authorization Required: ${widget.capability}</div>
                <div style="font-size: 12px; margin: 4px 0;">Target: <code>${widget.resource}</code></div>
                <div class="diff-container">${widget.diff_preview || 'No diff preview'}</div>
                <div class="approval-actions">
                    <button class="btn-approve" onclick="handleApprovalAction('${widget.request_id}', 'approve', this)">Authorize</button>
                    <button class="btn-deny" onclick="handleApprovalAction('${widget.request_id}', 'deny', this)">Deny</button>
                </div>
            `;

        } else if (widget.widget === 'AUDIO_PLAYER') {
            container.innerHTML = `
                <div style="display: flex; align-items: center; gap: 10px;">
                    <button class="action-btn-small" onclick="speakText('${widget.text_content}')">▶ Listen</button>
                    <div>
                        <div class="widget-title" style="margin: 0;">🎙️ ${widget.title}</div>
                        <div style="font-size: 11px; color: var(--text-muted);">${widget.text_content.slice(0, 60)}...</div>
                    </div>
                </div>
            `;
        }

        feed.appendChild(container);
        feed.scrollTop = feed.scrollHeight;
    }

    window.handleApprovalAction = async function(reqId, action, btn) {
        try {
            const res = await fetch('/api/capabilities/approve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ request_id: reqId, action: action })
            });
            const data = await res.json();
            if (data.status === 'SUCCESS') {
                const parent = btn.closest('.approval-actions');
                if (parent) {
                    parent.innerHTML = `<span style="font-size: 12px; color: ${action === 'approve' ? 'var(--cyan)' : 'var(--danger)'}; font-weight: 600;">✓ Capability ${action.toUpperCase()}D</span>`;
                }
                loadPendingApprovals();
                loadSecurityAudits();
            }
        } catch (e) {
            console.error('Error handling approval action:', e);
        }
    };

    // ---------------- LIVE SSE STREAMING ----------------
    function initSSE() {
        try {
            const sse = new EventSource('/api/stream');
            sse.onmessage = (event) => {
                try {
                    const parsed = JSON.parse(event.data);
                    if (parsed.event === 'widget') {
                        renderWidget(parsed.data);
                    } else if (parsed.event === 'execution_start') {
                        addHalLog(parsed.data.intent, parsed.data.thought);
                    } else if (parsed.event === 'execution_done') {
                        addHalLog(parsed.data.intent, `Done: ${parsed.data.result}`);
                    }
                } catch (e) {}
            };
            sse.onerror = () => {
                sse.close();
                setTimeout(initSSE, 6000);
            };
        } catch (e) {
            console.warn('SSE not supported on this connection');
        }
    }
    initSSE();

    // ---------------- SPEECH TO TEXT & SYNTHESIS ----------------
    function speakText(text) {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
            const u = new SpeechSynthesisUtterance(text);
            u.rate = 1.0;
            window.speechSynthesis.speak(u);
        }
    }

    if (micBtn) {
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRec) {
            const rec = new SpeechRec();
            rec.continuous = false;
            rec.interimResults = false;
            rec.onstart = () => micBtn.classList.add('listening');
            rec.onresult = (e) => {
                const transcript = e.results[0][0].transcript;
                if (userInput) userInput.value = transcript;
                micBtn.classList.remove('listening');
                dispatchIntent(transcript);
            };
            rec.onerror = () => micBtn.classList.remove('listening');
            rec.onend = () => micBtn.classList.remove('listening');

            micBtn.addEventListener('click', () => {
                try { rec.start(); } catch (e) { rec.stop(); }
            });
        } else {
            micBtn.style.opacity = '0.3';
            micBtn.title = 'Speech recognition not supported in browser';
        }
    }

    // ---------------- KNOWLEDGE & SEMANTIC FS ----------------
    const memorySearchInput = document.getElementById('memory-search-input');
    const btnSearchMemory = document.getElementById('btn-search-memory');
    const memorySearchResults = document.getElementById('memory-search-results');
    const indexedFilesList = document.getElementById('indexed-files-list');

    async function searchMemory() {
        const q = memorySearchInput ? memorySearchInput.value.trim() : '';
        if (!q) return;

        memorySearchResults.innerHTML = '<div class="placeholder-text">Searching vector embeddings...</div>';
        try {
            const res = await fetch(`/api/memory/search?q=${encodeURIComponent(q)}&k=5`);
            const data = await res.json();
            if (!data.results || data.results.length === 0) {
                memorySearchResults.innerHTML = '<div class="placeholder-text">No matching semantic vectors found.</div>';
                return;
            }

            let html = '';
            data.results.forEach((item, idx) => {
                html += `
                    <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-color); border-radius: 8px; padding: 10px; margin-bottom: 8px;">
                        <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px;">
                            <strong>${item.path}</strong>
                            <span class="highlight-cyan">Similarity: ${(item.similarity * 100).toFixed(1)}%</span>
                        </div>
                        <div style="font-size: 12px; color: var(--text-secondary); line-height: 1.4;">${item.content}</div>
                    </div>
                `;
            });
            memorySearchResults.innerHTML = html;
        } catch (e) {
            memorySearchResults.innerHTML = `<div class="placeholder-text" style="color: var(--danger);">Search error: ${e.message}</div>`;
        }
    }

    if (btnSearchMemory) btnSearchMemory.addEventListener('click', searchMemory);
    if (memorySearchInput) {
        memorySearchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') searchMemory();
        });
    }

    async function loadIndexedFiles() {
        if (!indexedFilesList) return;
        try {
            const res = await fetch('/api/memory/files');
            const data = await res.json();
            if (!data.files || data.files.length === 0) {
                indexedFilesList.innerHTML = '<div class="placeholder-text">No files indexed yet.</div>';
                return;
            }
            let html = '<ul style="list-style: none; font-size: 12px; display: flex; flex-direction: column; gap: 6px;">';
            data.files.forEach(f => {
                html += `<li>📄 <code>${f}</code></li>`;
            });
            html += '</ul>';
            indexedFilesList.innerHTML = html;
        } catch (e) {
            indexedFilesList.innerHTML = '<div class="placeholder-text">Failed to load indexed files.</div>';
        }
    }

    // Knowledge Graph
    const graphQueryInput = document.getElementById('graph-query-input');
    const btnQueryGraph = document.getElementById('btn-query-graph');
    const graphAnswerBox = document.getElementById('graph-answer-box');
    const tripletContainer = document.getElementById('triplet-table-container');
    const btnRefreshGraph = document.getElementById('btn-refresh-graph');

    async function queryGraph() {
        const q = graphQueryInput ? graphQueryInput.value.trim() : '';
        if (!q) return;
        graphAnswerBox.innerHTML = '<div class="placeholder-text">Traversing knowledge graph relations...</div>';
        try {
            const res = await fetch(`/api/graph/query?q=${encodeURIComponent(q)}`);
            const data = await res.json();
            graphAnswerBox.innerHTML = `<div style="font-size: 13px; line-height: 1.5; color: var(--cyan); white-space: pre-wrap;">${data.answer}</div>`;
        } catch (e) {
            graphAnswerBox.innerHTML = `<div class="placeholder-text" style="color: var(--danger);">Query error: ${e.message}</div>`;
        }
    }

    if (btnQueryGraph) btnQueryGraph.addEventListener('click', queryGraph);
    if (graphQueryInput) {
        graphQueryInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') queryGraph();
        });
    }

    async function loadGraphSnapshot() {
        if (!tripletContainer) return;
        try {
            const res = await fetch('/api/graph/snapshot?limit=30');
            const data = await res.json();
            if (!data.edges || data.edges.length === 0) {
                tripletContainer.innerHTML = '<div class="placeholder-text">Knowledge graph currently empty. Ingest text or chat to populate relations.</div>';
                return;
            }

            let html = `
                <table class="data-table">
                    <thead>
                        <tr><th>Subject</th><th>Relation</th><th>Object</th><th>Context</th></tr>
                    </thead>
                    <tbody>
            `;
            data.edges.forEach(e => {
                html += `
                    <tr>
                        <td><strong>${e.source}</strong></td>
                        <td><span class="badge" style="background: rgba(168,85,247,0.15); color: var(--purple);">${e.relation}</span></td>
                        <td><strong>${e.target}</strong></td>
                        <td style="color: var(--text-muted); font-size: 11px;">${(e.context || '').slice(0, 40)}</td>
                    </tr>
                `;
            });
            html += '</tbody></table>';
            tripletContainer.innerHTML = html;
        } catch (e) {
            tripletContainer.innerHTML = '<div class="placeholder-text">Failed to load graph snapshot.</div>';
        }
    }

    if (btnRefreshGraph) btnRefreshGraph.addEventListener('click', loadGraphSnapshot);

    // ---------------- SECURITY & CAPABILITY APPROVALS ----------------
    const pendingList = document.getElementById('pending-approvals-list');
    const auditTableBody = document.getElementById('audit-table-body');

    async function loadPendingApprovals() {
        try {
            const res = await fetch('/api/capabilities/pending');
            const data = await res.json();
            const pending = data.pending || [];

            if (pendingBadge) {
                if (pending.length > 0) {
                    pendingBadge.innerText = pending.length;
                    pendingBadge.style.display = 'inline-block';
                } else {
                    pendingBadge.style.display = 'none';
                }
            }

            if (!pendingList) return;
            if (pending.length === 0) {
                pendingList.innerHTML = '<div class="placeholder-text">No pending authorizations. System operating in safe state.</div>';
                return;
            }

            let html = '';
            pending.forEach(item => {
                html += `
                    <div class="approval-card canvas-widget" style="margin-bottom: 12px;">
                        <div class="widget-title" style="color: var(--warning);">⚠️ Authorization Required: ${item.capability}</div>
                        <div style="font-size: 12px; margin: 4px 0;">Target: <code>${item.resource}</code></div>
                        <div class="diff-container">${item.diff || 'No diff'}</div>
                        <div class="approval-actions">
                            <button class="btn-approve" onclick="handleApprovalAction('${item.request_id}', 'approve', this)">Authorize Action</button>
                            <button class="btn-deny" onclick="handleApprovalAction('${item.request_id}', 'deny', this)">Deny Action</button>
                        </div>
                    </div>
                `;
            });
            pendingList.innerHTML = html;
        } catch (e) {
            console.error('Error loading pending approvals:', e);
        }
    }

    async function loadSecurityAudits() {
        if (!auditTableBody) return;
        try {
            const res = await fetch('/api/capabilities/audit');
            const data = await res.json();
            const audits = data.audit || [];

            if (audits.length === 0) {
                auditTableBody.innerHTML = '<tr><td colspan="6" class="placeholder-text">No audit events recorded yet.</td></tr>';
                return;
            }

            let html = '';
            audits.reverse().forEach(a => {
                const dateStr = new Date(a.timestamp * 1000).toLocaleTimeString();
                const isApproved = a.action === 'APPROVED' || a.action === 'AUTO_APPROVED' || a.action === 'GRANTED';
                html += `
                    <tr>
                        <td style="color: var(--text-muted);">${dateStr}</td>
                        <td><code>${a.request_id}</code></td>
                        <td><span class="badge" style="background: rgba(255,255,255,0.05);">${a.capability}</span></td>
                        <td><code>${a.resource}</code></td>
                        <td><span class="badge" style="background: ${isApproved ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'}; color: ${isApproved ? 'var(--success)' : 'var(--danger)'};">${a.action}</span></td>
                        <td style="color: var(--text-secondary);">${a.reason}</td>
                    </tr>
                `;
            });
            auditTableBody.innerHTML = html;
        } catch (e) {
            auditTableBody.innerHTML = '<tr><td colspan="6" class="placeholder-text">Failed to load audit history.</td></tr>';
        }
    }

    // ---------------- CODE SANDBOX STUDIO ----------------
    const sandboxCodeEditor = document.getElementById('sandbox-code-editor');
    const btnRunSandbox = document.getElementById('btn-run-sandbox');
    const sandboxStatusBadge = document.getElementById('sandbox-status-badge');
    const sandboxDuration = document.getElementById('sandbox-duration');
    const sandboxStdout = document.getElementById('sandbox-stdout');
    const sandboxStderr = document.getElementById('sandbox-stderr');
    const sandboxResult = document.getElementById('sandbox-result');

    if (btnRunSandbox && sandboxCodeEditor) {
        btnRunSandbox.addEventListener('click', async () => {
            const code = sandboxCodeEditor.value;
            sandboxStatusBadge.innerText = 'EXECUTING';
            sandboxStatusBadge.style.background = 'rgba(245, 158, 11, 0.2)';
            sandboxStatusBadge.style.color = 'var(--warning)';

            try {
                const res = await fetch('/api/sandbox/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code: code })
                });
                const data = await res.json();
                sandboxStatusBadge.innerText = data.status || 'DONE';
                sandboxStatusBadge.style.background = data.status === 'SUCCESS' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)';
                sandboxStatusBadge.style.color = data.status === 'SUCCESS' ? 'var(--success)' : 'var(--danger)';

                sandboxDuration.innerText = `Duration: ${data.duration_ms || 0} ms`;
                sandboxStdout.innerText = data.stdout || '(No stdout)';
                sandboxStderr.innerText = data.stderr || 'None.';
                sandboxResult.innerText = data.result !== null ? JSON.stringify(data.result) : 'None';
            } catch (e) {
                sandboxStatusBadge.innerText = 'ERROR';
                sandboxStderr.innerText = e.message;
            }
        });
    }

    // ---------------- SWARM & TELEMETRY ----------------
    const swarmNodeId = document.getElementById('swarm-node-id');
    const swarmPort = document.getElementById('swarm-port');
    const swarmCountBadge = document.getElementById('swarm-count-badge');
    const swarmPeerList = document.getElementById('swarm-peer-list');
    const headerPeers = document.getElementById('header-peers');
    const swarmBroadcastInput = document.getElementById('swarm-broadcast-input');
    const btnBroadcastSwarm = document.getElementById('btn-broadcast-swarm');
    const btnRefreshTelemetry = document.getElementById('btn-refresh-telemetry');

    async function loadSwarmStatus() {
        try {
            const res = await fetch('/api/swarm/status');
            const data = await res.json();

            if (swarmNodeId) swarmNodeId.innerText = data.node_id || 'Active';
            if (swarmPort) swarmPort.innerText = data.broadcast_port || '5005';
            if (swarmCountBadge) swarmCountBadge.innerText = `${data.peer_count} Peers`;
            if (headerPeers) headerPeers.innerText = `${data.peer_count} Peers`;

            if (swarmPeerList) {
                if (!data.peers || data.peers.length === 0) {
                    swarmPeerList.innerHTML = '<div class="placeholder-text">Listening for peer heartbeats on UDP 5005...</div>';
                } else {
                    let html = '<ul style="list-style: none; display: flex; flex-direction: column; gap: 8px;">';
                    data.peers.forEach(p => {
                        html += `
                            <li style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-color); border-radius: 8px; padding: 10px; font-size: 12px; display: flex; justify-content: space-between;">
                                <div><strong>${p.node_id}</strong> (${p.host}:${p.port})</div>
                                <span class="badge" style="background: rgba(16,185,129,0.2); color: var(--success);">ONLINE</span>
                            </li>
                        `;
                    });
                    html += '</ul>';
                    swarmPeerList.innerHTML = html;
                }
            }
        } catch (e) {}
    }

    if (btnBroadcastSwarm && swarmBroadcastInput) {
        btnBroadcastSwarm.addEventListener('click', async () => {
            const text = swarmBroadcastInput.value.trim();
            if (!text) return;
            try {
                await fetch('/api/swarm/broadcast', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: { type: 'GOSSIP', payload: text } })
                });
                swarmBroadcastInput.value = '';
                addHalLog('SWARM_BROADCAST', text);
            } catch (e) {}
        });
    }

    async function loadTelemetry() {
        try {
            const res = await fetch('/api/system/stats');
            const data = await res.json();
            const mem = data.memory_tiers || {};
            const sys = data.telemetry || {};

            // Memory tiers
            const l1Turns = mem.l1_active_turns || 0;
            const l1Tokens = mem.l1_token_usage || 0;
            const l1Max = mem.l1_max_budget || 8192;
            const l2Entries = mem.l2_episodic_entries || 0;
            const pageFaults = mem.total_page_faults || 0;
            const swaps = mem.total_swaps || 0;

            const l1Usage = document.getElementById('l1-usage');
            const l1Progress = document.getElementById('l1-progress');
            if (l1Usage) l1Usage.innerText = `${l1Tokens} / ${l1Max} tok`;
            if (l1Progress) {
                const pct = Math.min(100, Math.round((l1Tokens / l1Max) * 100));
                l1Progress.style.width = `${pct}%`;
            }

            const tierL1Turns = document.getElementById('tier-l1-turns');
            const tierL2Count = document.getElementById('tier-l2-count');
            if (tierL1Turns) tierL1Turns.innerText = l1Turns;
            if (tierL2Count) tierL2Count.innerText = l2Entries;

            const telOs = document.getElementById('telemetry-os');
            const telFaults = document.getElementById('telemetry-page-faults');
            const telSwaps = document.getElementById('telemetry-swaps');
            const telBudget = document.getElementById('telemetry-budget');

            if (telOs) telOs.innerText = sys.os || 'Windows';
            if (telFaults) telFaults.innerText = pageFaults;
            if (telSwaps) telSwaps.innerText = swaps;
            if (telBudget) telBudget.innerText = l1Max.toLocaleString();

        } catch (e) {}
    }

    if (btnRefreshTelemetry) btnRefreshTelemetry.addEventListener('click', loadTelemetry);

    // Initial Bootstrap
    loadTelemetry();
    loadSwarmStatus();
    loadPendingApprovals();

    // Auto Refresh Intervals
    setInterval(loadSwarmStatus, 8000);
    setInterval(loadPendingApprovals, 5000);
});
