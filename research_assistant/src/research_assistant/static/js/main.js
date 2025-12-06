document.addEventListener('DOMContentLoaded', () => {
    const researchForm = document.getElementById('researchForm');
    const startBtn = document.getElementById('startBtn');
    const terminalContent = document.getElementById('terminalContent');
    const statusBadge = document.getElementById('statusBadge');
    const markdownViewer = document.getElementById('markdownViewer');
    const downloadBtn = document.getElementById('downloadBtn');

    let eventSource = null;

    // Auto-scroll terminal
    const scrollToBottom = () => {
        terminalContent.scrollTop = terminalContent.scrollHeight;
    };

    const appendLog = (text) => {
        if (!text) return;
        const line = document.createElement('div');
        line.className = 'log-line';
        line.textContent = text; // Secure text content
        terminalContent.appendChild(line);
        scrollToBottom();
    };

    const updateStatus = (status) => {
        statusBadge.textContent = status;
        statusBadge.className = `status-badge ${status}`;

        if (status === 'RUNNING') {
            startBtn.classList.add('loading');
            startBtn.disabled = true;
            downloadBtn.classList.add('disabled');
        } else {
            startBtn.classList.remove('loading');
            startBtn.disabled = false;
        }

        if (status === 'COMPLETED') {
            fetchResult();
        }
    };

    const fetchResult = async () => {
        try {
            const res = await fetch('/api/result');
            const data = await res.json();

            if (data.markdown) {
                // Parse markdown
                markdownViewer.innerHTML = marked.parse(data.markdown);
            }

            if (data.downloadUrl) {
                downloadBtn.href = data.downloadUrl;
                downloadBtn.classList.remove('disabled');
            }

        } catch (e) {
            console.error("Error fetching result:", e);
        }
    };

    const startStreaming = () => {
        if (eventSource) eventSource.close();

        eventSource = new EventSource('/api/status');

        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.log) {
                appendLog(data.log);
            }

            if (data.status) {
                updateStatus(data.status);
                // Stop streaming if done
                if (data.status === 'COMPLETED' || data.status === 'FAILED') {
                    eventSource.close();
                }
            }
        };

        eventSource.onerror = () => {
            // Connection closed or error
            eventSource.close();
        };
    };

    researchForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const topic = document.getElementById('topic').value;
        const outputPath = document.getElementById('outputPath').value;

        if (!topic) return;

        // Clear UI
        terminalContent.innerHTML = '<span class="log-line system">> Starting new research session...</span>';
        markdownViewer.innerHTML = '<div class="empty-state"><p>Research in progress...</p></div>';

        try {
            const res = await fetch('/api/research', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic, outputPath })
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
    });
});
