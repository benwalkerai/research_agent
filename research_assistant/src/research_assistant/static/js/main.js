document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const researchForm = document.getElementById('researchForm');
    const startBtn = document.getElementById('startBtn'); // sidebar btn
    const stopBtn = document.getElementById('stopBtn'); // [NEW]
    const terminalContent = document.getElementById('terminal-output'); // Fixed ID
    const statusBadge = document.getElementById('statusBadge');
    const markdownViewer = document.getElementById('markdownViewer'); // Need to check HTML for this one too?
    const downloadBtn = document.getElementById('downloadBtn');
    const depthRange = document.getElementById('depthRange'); // name=depth in HTML check ID?
    const depthLabel = document.getElementById('depthLabel');
    const liveActivity = document.getElementById('liveActivity'); // check HTML
    const terminalPanel = document.getElementById('terminalPanel'); // check HTML
    const terminalToggle = document.getElementById('terminalToggle'); // check HTML

    // New Elements
    const topicDisplay = document.getElementById('sidebar-topic'); // ID in HTML is sidebar-topic
    const heroInput = document.getElementById('heroInput');
    const heroStartBtn = document.getElementById('heroStartBtn');
    const heroSection = document.getElementById('hero-view'); // Fixed ID
    const activeResearchView = document.getElementById('active-view'); // Fixed ID
    const workspaceHeader = document.getElementById('workspaceHeader'); // check HTML
    const reasoningContent = document.getElementById('reasoningContent'); // check HTML
    const reasoningAccordion = document.getElementById('reasoningAccordion'); // check HTML
    const citationRail = document.getElementById('citationRail'); // check HTML

    // --- Slider Logic ---
    const depthMap = { 1: 'Fast', 2: 'Normal', 3: 'Deep' };
    const updateDepthLabel = () => {
        const val = parseInt(depthRange.value);
        if (depthLabel) {
            depthLabel.textContent = depthMap[val];
            depthLabel.className = `highlight ${depthMap[val].toLowerCase()}`;
        }
    };
    if (depthRange) depthRange.addEventListener('input', updateDepthLabel);

    // --- Collapsible Terminal ---
    window.toggleTerminal = () => {
        if (terminalPanel) {
            terminalPanel.classList.toggle('collapsed');
            terminalPanel.classList.toggle('expanded');
        }
    };
    if (terminalToggle) {
        terminalToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            window.toggleTerminal();
        });
    }

    // --- Accordion Logic ---
    window.toggleReasoning = () => {
        if (reasoningAccordion) reasoningAccordion.classList.toggle('closed');
    };

    // --- View Switching ---
    const switchToActiveView = (topic) => {
        if (heroSection) heroSection.classList.add('hidden');
        if (activeResearchView) activeResearchView.classList.remove('hidden');
        if (workspaceHeader) workspaceHeader.classList.remove('hidden');
        if (topicDisplay) topicDisplay.value = topic;

        // Reset UI
        if (reasoningContent) reasoningContent.innerHTML = '';
        if (liveActivity) liveActivity.innerHTML = '';
        if (citationRail) citationRail.innerHTML = '<h4>Sources</h4>';
        if (markdownViewer) markdownViewer.innerHTML = '<div class="empty-state"><div class="empty-icon">⚛</div><p>Initializing neural pathways...</p></div>';
    };

    // --- Live Activity Stream ---
    const addActivityCard = (text, type = 'info') => {
        if (!liveActivity) return;

        const card = document.createElement('div');
        card.className = `activity-card ${type}`;

        let icon = 'ℹ️';
        if (type === 'scanning') icon = '🔍';
        if (type === 'reading') icon = '📖';
        if (type === 'writing') icon = '✍️';
        if (type === 'error') icon = '❌';
        if (type === 'success') icon = '✅';

        const cleanText = text.replace(/\[.*?\]/g, '').replace(/"/g, '').trim();
        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        card.innerHTML = `
            <div class="activity-icon">${icon}</div>
            <div class="activity-content">
                <div class="activity-title">${cleanText}</div>
                <div class="activity-meta">${timestamp}</div>
            </div>
        `;

        liveActivity.appendChild(card);
        liveActivity.scrollTop = liveActivity.scrollHeight;
    };

    const addReasoningStep = (text) => {
        if (!reasoningContent) return;
        const step = document.createElement('div');
        step.className = 'reasoning-step';
        if (text.includes('✨')) step.classList.add('highlight');
        step.textContent = text.replace(/>/g, '').trim();
        reasoningContent.appendChild(step);
        reasoningContent.scrollTop = reasoningContent.scrollHeight;
    };

    // --- Citation Extraction ---
    const updateCitations = (markdownText) => {
        if (!citationRail) return;
        const regex = /\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g;
        let match;
        const seenUrls = new Set();

        citationRail.innerHTML = '<h4>Sources</h4>';

        while ((match = regex.exec(markdownText)) !== null) {
            const title = match[1];
            const url = match[2];

            if (!seenUrls.has(url)) {
                seenUrls.add(url);
                try {
                    const hostname = new URL(url).hostname;
                    const card = document.createElement('a');
                    card.href = url;
                    card.target = "_blank";
                    card.className = 'citation-card';
                    card.innerHTML = `
                        <div class="citation-icon">
                            <img src="https://www.google.com/s2/favicons?domain=${url}" width="16" height="16" alt="icon">
                        </div>
                        <div class="citation-info">
                            <div class="citation-title">${title}</div>
                            <div class="citation-url">${hostname}</div>
                        </div>
                    `;
                    citationRail.appendChild(card);
                } catch (e) { console.error("Invalid URL:", url); }
            }
        }
    };

    // --- Terminal Logic & Rich Parsing ---
    let eventSource = null;
    const scrollToBottom = () => { if (terminalContent) terminalContent.scrollTop = terminalContent.scrollHeight; };

    const updateStatus = (status) => {
        if (!statusBadge) return;
        statusBadge.textContent = status;
        statusBadge.className = `px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase ${status === 'RUNNING' ? 'bg-amber-500/20 text-amber-500 border border-amber-500/50 animate-pulse' :
            status === 'COMPLETED' ? 'bg-emerald-500/20 text-emerald-500 border border-emerald-500/50' :
                'bg-slate-700 text-slate-400'
            }`;
    };

    const fetchResult = async () => {
        if (!markdownViewer) return;
        try {
            const res = await fetch('/api/result-fragment');
            const html = await res.text();
            markdownViewer.innerHTML = html;

            // [NEW] Scan for citations
            const links = markdownViewer.querySelectorAll('a');
            const uniqueSources = new Set();
            links.forEach(link => {
                if (link.href && link.href.startsWith('http')) {
                    uniqueSources.add(link.href);
                }
            });

            if (uniqueSources.size > 0 && citationRail) {
                let html = '<h4>Sources</h4>';
                uniqueSources.forEach(src => {
                    try {
                        const url = new URL(src);
                        html += `<a href="${src}" target="_blank" class="block p-2 bg-slate-900/50 rounded border border-white/5 text-[10px] text-indigo-400 truncate hover:bg-slate-800 transition-colors mb-2">
                                    <div class="font-bold">${url.hostname}</div>
                                    <div class="opacity-50 truncate">${url.pathname}</div>
                                 </a>`;
                    } catch (e) { }
                });
                citationRail.innerHTML = html;
            }

        } catch (e) {
            console.error("Error fetching result:", e);
            markdownViewer.innerHTML = "<div class='text-red-500'>Failed to load report.</div>";
        }
    };


    const appendLog = (text) => {
        if (!terminalContent || !text) return;
        text = text.trim();
        if (!text) return;

        let el = document.createElement('div');
        el.className = 'log-line opacity-80 mb-1'; // Default

        // 1. Divider / Phase Change
        if (text.includes('---') || text.includes('Execute')) {
            el.className = 'text-center text-xs text-slate-500 font-bold uppercase tracking-widest my-4 border-b border-white/5 pb-2';
            el.textContent = text.replace(/[-]/g, '').trim();
        }
        // 2. Headings / Roles
        else if (text.match(/^(Role|Task|Agent):/i)) {
            el.className = 'text-indigo-400 font-bold mt-2';
            el.textContent = text;
        }
        // 3. Thoughts (The internal monologue)
        // 3. Thoughts (The internal monologue)
        // Relaxed match: Check if it contains "Thought:" anywhere
        else if (text.includes('Thought:')) {
            el.className = 'pl-3 border-l-2 border-slate-600 italic text-slate-400 my-2 text-[11px]';
            el.textContent = text;
            addReasoningStep(text);
            addActivityCard('Thinking...', 'scanning');
        }
        // 4. Action (Tool Usage)
        else if (text.includes('Action:')) {
            el.className = 'text-cyan-400 font-bold mt-2 flex items-center gap-2';
            el.innerHTML = `<span>⚡</span> ${text}`;
            addActivityCard('Using Tool', 'reading');
        }
        // 5. Action Input (Argument)
        else if (text.match(/^\s*Action Input:/i)) {
            el.className = 'bg-slate-900/50 p-2 rounded text-indigo-300 font-mono text-[10px] ml-4 border border-white/5';
            try {
                // Try to pretty print JSON input if possible
                const jsonPart = text.replace(/Action Input:/i, '').trim();
                const obj = JSON.parse(jsonPart);
                el.innerHTML = `<span class="opacity-50">Input:</span> <pre>${JSON.stringify(obj, null, 2)}</pre>`;
            } catch (e) {
                el.textContent = text;
            }
        }
        // 6. Errors
        else if (text.toLowerCase().includes('error') || text.toLowerCase().includes('failed')) {
            el.className = 'text-red-400 bg-red-400/10 p-2 rounded border border-red-400/20 my-1';
            el.textContent = text;
        }
        // 7. General Log
        else {
            el.textContent = text;
        }

        terminalContent.appendChild(el);
        scrollToBottom();

        // Also stream to Activity Cards (if relevant)
        const lower = text.toLowerCase();
        if (lower.startsWith('thought')) addActivityCard('Thinking...', 'scanning');
        if (lower.startsWith('action:')) addActivityCard('Using Tool', 'reading');
    };

    const startStreaming = () => {
        if (eventSource) eventSource.close();

        // Connect to the correct endpoint
        eventSource = new EventSource('/api/events');

        eventSource.addEventListener('log', (e) => {
            const data = JSON.parse(e.data);
            appendLog(data.log);
        });

        eventSource.addEventListener('status', (e) => {
            updateStatus(e.data);
            // If completed, we might want to close, but app.py handles 'completed' event too.
        });

        eventSource.addEventListener('completed', (e) => {
            console.log("Research Completed");
            eventSource.close();
            fetchResult();
        });

        eventSource.onerror = () => {
            console.log("SSE Connection Closed/Error");
            eventSource.close();
        };
    };

    // --- Initiation Logic ---
    const startResearch = async (topic) => {
        console.log("startResearch called for:", topic);
        if (!topic) return;

        const outputPath = document.getElementById('outputPath')?.value || 'Research';
        const depthVal = document.getElementById('depthRange')?.value || 2;
        const depth = depthMap[depthVal]?.toLowerCase() || 'normal';

        switchToActiveView(topic);
        addActivityCard(`Initializing scan: ${topic} (${depth})`, 'scanning');

        try {
            const res = await fetch('/api/start-research', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({ topic, outputPath, depth })
            });
            const data = await res.json();

            if (data.status === 'started') {
                updateStatus('RUNNING');
                startStreaming();
            } else {
                alert(data.message || 'Failed to start.');
            }
        } catch (err) {
            console.error(err);
            alert('Error connecting to backend.');
        }
    };

    // --- Stop Logic ---
    if (stopBtn) {
        stopBtn.addEventListener('click', async () => {
            if (!confirm("Are you sure you want to stop the current research task?")) return;
            try {
                const res = await fetch('/api/stop-research', { method: 'POST' });
                const data = await res.json();
                if (data.status === 'stopping') {
                    updateStatus('STOPPING');
                    appendLog("🛑 User requested stop...");
                }
            } catch (e) {
                console.error(e);
            }
        });
    }

    // Handle standard form submit
    const standardForm = document.getElementById('researchForm');
    if (standardForm) {
        standardForm.addEventListener('submit', (e) => {
            e.preventDefault();
            console.log("Form submitted via sidebar");
        });
    }

    // Handle Hero Form Submit
    const heroForm = document.getElementById('heroForm');
    if (heroForm) {
        heroForm.addEventListener('submit', (e) => {
            e.preventDefault();
            console.log("Hero form submitted");
            const val = heroInput.value.trim();
            if (val) startResearch(val);
        });
    } else {
        console.error("Hero form not found!");
    }

    // Handle Hero Input (Backup)
    const handleHeroSubmit = () => {
        const val = heroInput.value.trim();
        if (val) startResearch(val);
    };

    if (heroStartBtn) {
        heroStartBtn.addEventListener('click', handleHeroSubmit);
    }
    if (heroInput) {
        heroInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') handleHeroSubmit();
        });
    }
});
