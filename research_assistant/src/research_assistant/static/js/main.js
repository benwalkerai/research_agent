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

    // --- Neural Network Animation ---
    let neuralAnimationInterval = null;
    let neuralNodes = [];
    let neuralConnections = [];
    let dataPulses = [];

    const startNeuralAnimation = () => {
        if (!markdownViewer) return;

        // Create neural network container
        const networkContainer = document.createElement('div');
        networkContainer.className = 'neural-network';
        networkContainer.id = 'neuralNetwork';

        // Create SVG for connections and pulses
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '100%');
        svg.setAttribute('height', '100%');
        svg.style.position = 'absolute';
        svg.style.top = '0';
        svg.style.left = '0';

        // Add gradient definition for connections
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        const gradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
        gradient.setAttribute('id', 'connectionGradient');
        gradient.innerHTML = `
            <stop offset="0%" stop-color="rgba(99, 102, 241, 0.6)" />
            <stop offset="50%" stop-color="rgba(6, 182, 212, 0.8)" />
            <stop offset="100%" stop-color="rgba(99, 102, 241, 0.6)" />
        `;
        defs.appendChild(gradient);

        // Add glow filter for pulses
        const glowFilter = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
        glowFilter.setAttribute('id', 'pulseGlow');
        glowFilter.innerHTML = `
            <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
            <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
            </feMerge>
        `;
        defs.appendChild(glowFilter);
        svg.appendChild(defs);
        networkContainer.appendChild(svg);

        const width = markdownViewer.offsetWidth;
        const height = markdownViewer.offsetHeight;

        // Reset state
        neuralNodes = [];
        neuralConnections = [];
        dataPulses = [];

        // Create STRUCTURED layered neural network
        // Layers: Input (8) -> Hidden1 (12) -> Hidden2 (10) -> Hidden3 (8) -> Output (6)
        const layers = [
            { count: 8, x: width * 0.1 },
            { count: 12, x: width * 0.3 },
            { count: 10, x: width * 0.5 },
            { count: 8, x: width * 0.7 },
            { count: 6, x: width * 0.9 }
        ];

        const layerNodes = []; // 2D array: layerNodes[layerIndex][nodeIndex]

        // Create nodes for each layer
        layers.forEach((layer, layerIndex) => {
            const nodesInLayer = [];
            const spacing = height / (layer.count + 1);

            for (let i = 0; i < layer.count; i++) {
                const node = document.createElement('div');

                // Vary sizes - input/output smaller, hidden layers larger
                let sizeClass = 'medium';
                if (layerIndex === 0 || layerIndex === layers.length - 1) {
                    sizeClass = 'small';
                } else if (layerIndex === 1 || layerIndex === 2) {
                    sizeClass = Math.random() > 0.5 ? 'large' : 'medium';
                }

                node.className = `neural-node ${sizeClass}`;

                const x = layer.x + (Math.random() - 0.5) * 20; // Small jitter
                const y = spacing * (i + 1) + (Math.random() - 0.5) * 10;

                node.style.left = `${x}px`;
                node.style.top = `${y}px`;
                node.style.animationDelay = `${Math.random() * 2}s`;

                networkContainer.appendChild(node);

                const nodeData = {
                    x, y,
                    baseX: x,  // Store original position for subtle drift
                    baseY: y,
                    vx: (Math.random() - 0.5) * 0.3,
                    vy: (Math.random() - 0.5) * 0.3,
                    element: node,
                    layer: layerIndex
                };

                nodesInLayer.push(nodeData);
                neuralNodes.push(nodeData);
            }
            layerNodes.push(nodesInLayer);
        });

        // Connect adjacent layers (each node connects to several nodes in next layer)
        for (let l = 0; l < layerNodes.length - 1; l++) {
            const currentLayer = layerNodes[l];
            const nextLayer = layerNodes[l + 1];

            currentLayer.forEach(nodeA => {
                // Connect to 3-5 nodes in the next layer
                const connectionCount = Math.floor(Math.random() * 3) + 3;
                const shuffled = [...nextLayer].sort(() => Math.random() - 0.5);

                for (let c = 0; c < Math.min(connectionCount, shuffled.length); c++) {
                    const nodeB = shuffled[c];

                    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                    line.setAttribute('x1', nodeA.x);
                    line.setAttribute('y1', nodeA.y);
                    line.setAttribute('x2', nodeB.x);
                    line.setAttribute('y2', nodeB.y);
                    line.classList.add('neural-connection');

                    // Random strength
                    if (Math.random() > 0.6) {
                        line.classList.add('strong');
                    }

                    line.style.animationDelay = `${Math.random() * 2}s`;
                    svg.appendChild(line);

                    neuralConnections.push({
                        line,
                        nodeA,
                        nodeB
                    });
                }
            });
        }

        // Create data pulses that flow LEFT to RIGHT through the network
        const pulseCount = 20;
        for (let i = 0; i < pulseCount; i++) {
            if (neuralConnections.length === 0) break;

            const conn = neuralConnections[Math.floor(Math.random() * neuralConnections.length)];
            const pulse = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            pulse.setAttribute('r', '4');
            pulse.classList.add('data-pulse');
            pulse.setAttribute('filter', 'url(#pulseGlow)');
            pulse.setAttribute('cx', conn.nodeA.x);
            pulse.setAttribute('cy', conn.nodeA.y);
            svg.appendChild(pulse);

            dataPulses.push({
                element: pulse,
                connection: conn,
                progress: Math.random(),
                speed: 0.01 + Math.random() * 0.015,
                direction: 1  // Always flow forward (left to right)
            });
        }

        markdownViewer.innerHTML = '';
        markdownViewer.appendChild(networkContainer);

        // Thinking state variables
        let thinkingIntensity = 0.5;
        let intensityDirection = 1;
        let frameCount = 0;
        let lastBurstTime = 0;
        let activeNodes = new Set();

        // Main animation loop
        neuralAnimationInterval = setInterval(() => {
            frameCount++;

            // Breathing intensity - slowly oscillate thinking activity
            thinkingIntensity += 0.005 * intensityDirection;
            if (thinkingIntensity > 1) {
                thinkingIntensity = 1;
                intensityDirection = -1;
            } else if (thinkingIntensity < 0.3) {
                thinkingIntensity = 0.3;
                intensityDirection = 1;
            }

            // Random node activation (neurons firing)
            if (Math.random() < 0.15 * thinkingIntensity) {
                const randomNode = neuralNodes[Math.floor(Math.random() * neuralNodes.length)];
                if (!activeNodes.has(randomNode)) {
                    activeNodes.add(randomNode);
                    randomNode.element.classList.add('thinking');
                    randomNode.activationTime = frameCount;
                }
            }

            // Deactivate nodes after a short time
            activeNodes.forEach(node => {
                if (frameCount - node.activationTime > 15 + Math.random() * 20) {
                    node.element.classList.remove('thinking');
                    activeNodes.delete(node);
                }
            });

            // Periodic burst pattern - ripple effect through the network
            if (frameCount - lastBurstTime > 60 + Math.random() * 120) {
                lastBurstTime = frameCount;

                // Pick a random starting layer and trigger cascade
                const startLayer = Math.floor(Math.random() * 3);
                const layerNodesList = neuralNodes.filter(n => n.layer === startLayer);

                layerNodesList.forEach((node, i) => {
                    setTimeout(() => {
                        node.element.classList.add('burst');
                        setTimeout(() => node.element.classList.remove('burst'), 300);
                    }, i * 50);
                });

                // Cascade to next layers
                for (let l = startLayer + 1; l < 5; l++) {
                    const delay = (l - startLayer) * 150;
                    const layerN = neuralNodes.filter(n => n.layer === l);
                    layerN.forEach((node, i) => {
                        setTimeout(() => {
                            node.element.classList.add('burst');
                            setTimeout(() => node.element.classList.remove('burst'), 200);
                        }, delay + i * 30);
                    });
                }
            }

            // Random connection flash (synaptic firing)
            if (Math.random() < 0.1 * thinkingIntensity) {
                const randomConn = neuralConnections[Math.floor(Math.random() * neuralConnections.length)];
                randomConn.line.classList.add('firing');
                setTimeout(() => randomConn.line.classList.remove('firing'), 150);
            }

            // Subtle node drift (stay near base position)
            neuralNodes.forEach(node => {
                node.x += node.vx;
                node.y += node.vy;

                // Drift back toward base position
                const driftX = node.baseX - node.x;
                const driftY = node.baseY - node.y;
                node.vx += driftX * 0.01;
                node.vy += driftY * 0.01;

                // Dampen velocity
                node.vx *= 0.98;
                node.vy *= 0.98;

                // Add small random perturbation (more when thinking intensely)
                node.vx += (Math.random() - 0.5) * 0.05 * thinkingIntensity;
                node.vy += (Math.random() - 0.5) * 0.05 * thinkingIntensity;

                node.element.style.left = `${node.x}px`;
                node.element.style.top = `${node.y}px`;
            });

            // Update connection lines
            neuralConnections.forEach(conn => {
                conn.line.setAttribute('x1', conn.nodeA.x);
                conn.line.setAttribute('y1', conn.nodeA.y);
                conn.line.setAttribute('x2', conn.nodeB.x);
                conn.line.setAttribute('y2', conn.nodeB.y);
            });

            // Animate data pulses along connections
            dataPulses.forEach(pulse => {
                // Vary speed based on thinking intensity
                const currentSpeed = pulse.speed * (0.7 + thinkingIntensity * 0.6);
                pulse.progress += currentSpeed * pulse.direction;

                // When pulse reaches end, jump to a new connection (forward flow)
                if (pulse.progress >= 1) {
                    pulse.progress = 0;

                    // Find connections from the destination node's layer going forward
                    const currentNodeB = pulse.connection.nodeB;
                    const forwardConnections = neuralConnections.filter(c =>
                        c.nodeA === currentNodeB ||
                        (c.nodeA.layer === currentNodeB.layer && Math.random() > 0.7)
                    );

                    if (forwardConnections.length > 0) {
                        pulse.connection = forwardConnections[Math.floor(Math.random() * forwardConnections.length)];
                    } else {
                        // Loop back to start of network
                        const startConnections = neuralConnections.filter(c => c.nodeA.layer === 0);
                        if (startConnections.length > 0) {
                            pulse.connection = startConnections[Math.floor(Math.random() * startConnections.length)];
                        }
                    }
                }

                // Interpolate position
                const conn = pulse.connection;
                const px = conn.nodeA.x + (conn.nodeB.x - conn.nodeA.x) * pulse.progress;
                const py = conn.nodeA.y + (conn.nodeB.y - conn.nodeA.y) * pulse.progress;

                pulse.element.setAttribute('cx', px);
                pulse.element.setAttribute('cy', py);

                // Pulse size varies with intensity
                const pulseSize = 3 + thinkingIntensity * 3;
                pulse.element.setAttribute('r', pulseSize);
            });

        }, 30);
    };

    const stopNeuralAnimation = () => {
        const networkContainer = document.getElementById('neuralNetwork');
        if (networkContainer) {
            networkContainer.remove();
        }
        if (neuralAnimationInterval) {
            clearInterval(neuralAnimationInterval);
            neuralAnimationInterval = null;
        }
        neuralNodes = [];
        neuralConnections = [];
        dataPulses = [];
    };

    // --- Live Activity Stream ---
    let lastActivityText = '';
    let lastActivityTime = 0;
    const MAX_ACTIVITY_CARDS = 20;
    const ACTIVITY_THROTTLE_MS = 500; // Max 2 messages per second

    const addActivityCard = (text, type = 'info', skipDuplicateCheck = false) => {
        if (!liveActivity) return;

        // Throttle messages to prevent flooding
        const now = Date.now();
        if (!skipDuplicateCheck && (now - lastActivityTime) < ACTIVITY_THROTTLE_MS) {
            return;
        }
        lastActivityTime = now;

        // Deduplicate consecutive identical messages
        if (!skipDuplicateCheck && text === lastActivityText) {
            return;
        }
        lastActivityText = text;

        // Limit number of activity cards
        while (liveActivity.children.length >= MAX_ACTIVITY_CARDS) {
            liveActivity.removeChild(liveActivity.firstChild);
        }

        const card = document.createElement('div');
        card.className = `activity-card ${type}`;

        let icon = 'ℹ️';
        if (type === 'scanning') icon = '🔍';
        if (type === 'reading') icon = '📖';
        if (type === 'writing') icon = '✍️';
        if (type === 'error') icon = '❌';
        if (type === 'success') icon = '✅';
        if (type === 'thinking') icon = '💭';
        if (type === 'analyzing') icon = '🔬';
        if (type === 'planning') icon = '📋';
        if (type === 'searching') icon = '🌐';

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

    // Parse meaningful activity from log text with geeky movie references
    const parseActivityFromLog = (logText) => {
        const lower = logText.toLowerCase();

        // Extract search queries with geeky messages
        if (lower.includes('search_query') || lower.includes('searching for')) {
            const queryMatch = logText.match(/search_query[:\s]+["']?([^"'\n]+)["']?/i);
            if (queryMatch && queryMatch[1]) {
                const funPhrases = [
                    'Following the white rabbit',
                    'Accessing the mainframe',
                    'Hacking the Gibson for',
                    'Searching the archives for',
                    'Consulting the Oracle about'
                ];
                const phrase = funPhrases[Math.floor(Math.random() * funPhrases.length)];
                return { text: `${phrase}: ${queryMatch[1].substring(0, 45)}`, type: 'searching' };
            }
        }

        // Action Input parsing
        if (lower.includes('action input:')) {
            try {
                const jsonMatch = logText.match(/action input:\s*({.*})/i);
                if (jsonMatch) {
                    const input = JSON.parse(jsonMatch[1]);
                    if (input.search_query) {
                        return { text: `Entering the Matrix: ${input.search_query.substring(0, 45)}`, type: 'searching' };
                    }
                }
            } catch (e) {
                // Ignore parse errors
            }
        }

        // Phase changes with movie references
        if (lower.includes('strategy phase')) {
            return { text: '🎯 Plotting the heist (Ocean\'s Eleven style)', type: 'planning' };
        }
        if (lower.includes('research phase')) {
            return { text: '🚀 Entering the Matrix...', type: 'scanning' };
        }
        if (lower.includes('reporting phase')) {
            return { text: '📝 Compiling the mission briefing', type: 'writing' };
        }


        // Agent transitions with personality
        if (lower.includes('lead research strategist') || lower.includes('strategist')) {
            const phrases = [
                'Strategist channeling Yoda',
                'Planning like Tony Stark',
                'Strategizing the Death Star plans'
            ];
            return { text: phrases[Math.floor(Math.random() * phrases.length)], type: 'planning' };
        }
        if (lower.includes('senior researcher')) {
            const phrases = [
                'Researcher going full Sherlock',
                'Following breadcrumbs like Hansel',
                'Researcher channeling Indiana Jones',
                'Diving down the rabbit hole'
            ];
            return { text: phrases[Math.floor(Math.random() * phrases.length)], type: 'scanning' };
        }
        if (lower.includes('research analyst')) {
            const phrases = [
                'Analyst crunching numbers like Neo',
                'Decoding like Alan Turing',
                'Analyst seeing the Matrix',
                'Connecting dots like John Nash'
            ];
            return { text: phrases[Math.floor(Math.random() * phrases.length)], type: 'analyzing' };
        }
        if (lower.includes('content writer')) {
            const phrases = [
                'Writer channeling Shakespeare',
                'Crafting prose like Tolkien',
                'Writer weaving the tale',
                'Assembling the story arc'
            ];
            return { text: phrases[Math.floor(Math.random() * phrases.length)], type: 'writing' };
        }
        if (lower.includes('publisher')) {
            const phrases = [
                'Publisher making it so (Picard approved)',
                'Finalizing like a boss',
                'Publisher sealing the deal',
                'Ready for launch sequence'
            ];
            return { text: phrases[Math.floor(Math.random() * phrases.length)], type: 'success' };
        }

        // Thought patterns
        if (lower.includes('thought:')) {
            const thoughtMatch = logText.match(/thought:\s*(.+)/i);
            if (thoughtMatch && thoughtMatch[1]) {
                const thought = thoughtMatch[1].trim().substring(0, 70);
                if (thought.length > 10) {
                    return { text: `💭 ${thought}`, type: 'thinking' };
                }
            }
            const phrases = [
                'Pondering like The Thinker',
                'Deep in thought (Inception level)',
                'Contemplating the Force',
                'Processing... beep boop'
            ];
            return { text: phrases[Math.floor(Math.random() * phrases.length)], type: 'thinking' };
        }

        // Action patterns
        if (lower.includes('action:')) {
            const actionMatch = logText.match(/action:\s*(\w+)/i);
            if (actionMatch && actionMatch[1]) {
                return { text: `⚡ Activating ${actionMatch[1]} protocol`, type: 'reading' };
            }
        }

        // Completion indicators
        if (lower.includes('completed') || lower.includes('finished')) {
            const phrases = [
                '✨ Mission accomplished!',
                '🎉 Achievement unlocked',
                '✅ That\'s a wrap!',
                '🏁 Nailed it like Thor\'s hammer'
            ];
            return { text: phrases[Math.floor(Math.random() * phrases.length)], type: 'success' };
        }

        // Errors with humor
        if (lower.includes('error') || lower.includes('failed')) {
            const phrases = [
                '⚠️ Houston, we have a problem',
                '🔧 Hitting a plot twist',
                '⚡ Glitch in the Matrix detected',
                'Sorry Dave, I cannot help with that'
            ];
            return { text: phrases[Math.floor(Math.random() * phrases.length)], type: 'error' };
        }

        return null;
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

    // Track current agent for status display
    let currentAgent = 'IDLE';
    let researchStarted = false;

    const updateStatus = (status, agentName = null) => {
        if (!statusBadge) return;

        // Determine display text and styling
        let displayText = status;
        let styleClass = 'bg-slate-700 text-slate-400 border border-slate-600';

        if (status === 'IDLE') {
            displayText = 'IDLE';
            styleClass = 'bg-slate-700 text-slate-400 border border-slate-600';
        } else if (status === 'WARMING_UP') {
            displayText = 'Warming Up';
            styleClass = 'bg-blue-500/20 text-blue-400 border border-blue-500/50 animate-pulse';
        } else if (status === 'RUNNING') {
            if (agentName) {
                displayText = agentName;
                styleClass = 'bg-amber-500/20 text-amber-400 border border-amber-500/50 animate-pulse';
            } else {
                displayText = 'Running';
                styleClass = 'bg-amber-500/20 text-amber-500 border border-amber-500/50 animate-pulse';
            }
        } else if (status === 'COMPLETED' || status === 'FINISHED') {
            displayText = 'Finished';
            styleClass = 'bg-emerald-500/20 text-emerald-500 border border-emerald-500/50';
        } else if (status === 'FAILED') {
            displayText = 'Failed';
            styleClass = 'bg-red-500/20 text-red-500 border border-red-500/50';
        } else if (status === 'STOPPED' || status === 'STOPPING') {
            displayText = 'Stopped';
            styleClass = 'bg-orange-500/20 text-orange-500 border border-orange-500/50';
        }

        statusBadge.textContent = displayText;
        statusBadge.className = `px-2 py-0.5 rounded text-[10px] font-mono tracking-wider ${styleClass}`;
    };

    // Parse agent name from log text
    const parseAgentFromLog = (logText) => {
        const agentPatterns = [
            /Agent:\s*([A-Za-z\s]+)/i,
            /Working Agent:\s*([A-Za-z\s]+)/i,
            /\[([A-Za-z\s]+)\]\s*>/i,
            /^([A-Za-z\s]+):/,
        ];

        for (const pattern of agentPatterns) {
            const match = logText.match(pattern);
            if (match && match[1]) {
                const agentName = match[1].trim();
                const excludeTerms = ['Role', 'Task', 'Goal', 'Backstory', 'Action', 'Thought', 'Final', 'Input', 'Output'];
                if (!excludeTerms.includes(agentName)) {
                    return agentName;
                }
            }
        }

        const knownAgents = [
            'Lead Research Strategist',
            'Senior Researcher',
            'Research Analyst',
            'Content Writer',
            'Publisher'
        ];

        for (const agent of knownAgents) {
            if (logText.includes(agent)) {
                return agent;
            }
        }

        return null;
    };

    const fetchResult = async () => {
        if (!markdownViewer) return;

        // Stop neural network animation
        stopNeuralAnimation();

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

        // Parse agent name from log and update status
        const detectedAgent = parseAgentFromLog(text);
        if (detectedAgent && detectedAgent !== currentAgent) {
            currentAgent = detectedAgent;
            updateStatus('RUNNING', detectedAgent);
            addActivityCard(`${detectedAgent} is now working`, 'info', true);
        }

        // Parse meaningful activity from log
        const activity = parseActivityFromLog(text);
        if (activity) {
            addActivityCard(activity.text, activity.type);
        }

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
        else if (text.includes('Thought:')) {
            el.className = 'pl-3 border-l-2 border-slate-600 italic text-slate-400 my-2 text-[11px]';
            el.textContent = text;
            addReasoningStep(text);
        }
        // 4. Action (Tool Usage)
        else if (text.includes('Action:')) {
            el.className = 'text-cyan-400 font-bold mt-2 flex items-center gap-2';
            el.innerHTML = `<span>⚡</span> ${text}`;
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
            const backendStatus = e.data;

            // Map backend status to frontend display
            if (backendStatus === 'RUNNING' && !researchStarted) {
                researchStarted = true;
                updateStatus('WARMING_UP');
            } else if (backendStatus === 'RUNNING') {
                // Keep showing current agent (updated by appendLog)
                if (currentAgent === 'IDLE') {
                    updateStatus('RUNNING');
                } else {
                    updateStatus('RUNNING', currentAgent);
                }
            } else if (backendStatus === 'COMPLETED') {
                updateStatus('FINISHED');
                researchStarted = false;
                currentAgent = 'IDLE';
            } else if (backendStatus === 'FAILED') {
                updateStatus('FAILED');
                researchStarted = false;
                currentAgent = 'IDLE';
            } else if (backendStatus === 'STOPPED' || backendStatus === 'STOPPING') {
                updateStatus('STOPPED');
                researchStarted = false;
                currentAgent = 'IDLE';
            } else {
                updateStatus(backendStatus);
            }
        });

        eventSource.addEventListener('completed', (e) => {
            console.log("Research Completed");
            updateStatus('FINISHED');
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

        // Start neural network animation
        startNeuralAnimation();

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
                updateStatus('WARMING_UP');
                researchStarted = true;
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
