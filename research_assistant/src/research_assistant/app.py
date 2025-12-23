from flask import Flask, render_template, request, jsonify, Response, send_file
import threading
import queue
import time
import os
import sys
import io
import json
import re
import html
from dotenv import load_dotenv
import markdown2
try:
    from weasyprint import HTML  # Requires GTK/Pango/Cairo libs
    WEASYPRINT_AVAILABLE = True
    WEASYPRINT_IMPORT_ERROR = ""
except Exception as exc:
    HTML = None
    WEASYPRINT_AVAILABLE = False
    WEASYPRINT_IMPORT_ERROR = str(exc)
from research_assistant.crew import ResearchAssistant
import traceback
import shutil
from datetime import datetime, timedelta

import logging
from logging.handlers import RotatingFileHandler

# Define a lock for the log queue to ensure thread safety
log_lock = threading.Lock()

# Configure circular logging
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, "research_assistant.log")

# Create a separate logger for raw output to avoid interference with other loggers
raw_logger = logging.getLogger("raw_terminal")
raw_logger.setLevel(logging.INFO)
raw_logger.propagate = False  # Don't send to root logger

# Single RotatingFileHandler for all output
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(message)s'))
raw_logger.addHandler(file_handler)

class GlobalOutputRedirector:
    def __init__(self, original_stream, is_stderr=False):
        self.original_stream = original_stream
        self.is_stderr = is_stderr
        self._is_handling = threading.local()

    def write(self, data):
        if not hasattr(self._is_handling, 'active'):
            self._is_handling.active = False

        # Write to original stream (terminal)
        self.original_stream.write(data)
        self.original_stream.flush()

        if data.strip() and not self._is_handling.active:
            self._is_handling.active = True
            try:
                # 1. Write to file via raw_logger
                raw_logger.info(data.strip())
                
                # 2. Add to UI job_logs queue
                with log_lock:
                    job_logs.put(data)
            finally:
                self._is_handling.active = False

    def flush(self):
        self.original_stream.flush()

    def isatty(self):
        return self.original_stream.isatty()

# Initialize global redirectors
sys.stdout = GlobalOutputRedirector(sys.__stdout__)
sys.stderr = GlobalOutputRedirector(sys.__stderr__, is_stderr=True)

# Configure root logger to use stdout (which is now redirected)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

load_dotenv()

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUTPUTS_DIR = os.path.join(BASE_DIR, 'outputs')


def cleanup_old_outputs(folder_path: str, retention_days: int = 7) -> None:
    """
    Delete files (and empty folders) older than retention_days within folder_path.
    Runs on application start to keep outputs folder from growing indefinitely.
    """
    if not os.path.exists(folder_path):
        logger.info(f"Outputs directory not found, skipping cleanup: {folder_path}")
        return

    cutoff = datetime.now() - timedelta(days=retention_days)
    removed_files = 0
    removed_dirs = 0

    for root_dir, dirs, files in os.walk(folder_path, topdown=False):
        for file_name in files:
            file_path = os.path.join(root_dir, file_name)
            try:
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_mtime < cutoff:
                    os.remove(file_path)
                    removed_files += 1
            except Exception as exc:
                logger.warning(f"Failed to remove old output '{file_path}': {exc}")

        for dir_name in dirs:
            dir_path = os.path.join(root_dir, dir_name)
            try:
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    removed_dirs += 1
            except Exception as exc:
                logger.warning(f"Failed to cleanup empty folder '{dir_path}': {exc}")

    if removed_files or removed_dirs:
        logger.info(f"Outputs cleanup removed {removed_files} files and {removed_dirs} empty folders older than {retention_days} days.")


def _load_latest_markdown() -> str:
    """Return the latest markdown output from disk or memory."""
    global output_file_path, latest_research_output
    if output_file_path and os.path.exists(output_file_path):
        try:
            with open(output_file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as exc:
            logger.warning(f"Failed reading output file, falling back to in-memory content: {exc}")
    return str(latest_research_output or "").strip()


def _render_markdown_to_html(markdown_text: str) -> str:
    """Convert markdown text to HTML using the same extras as the live preview."""
    return markdown2.markdown(
        markdown_text or "",
        extras=['fenced-code-blocks', 'tables', 'break-on-newline']
    )


def _render_pdf_from_html(html_content: str) -> bytes:
    """Generate a PDF document from HTML content."""
    if not WEASYPRINT_AVAILABLE:
        raise RuntimeError(f"WeasyPrint unavailable: {WEASYPRINT_IMPORT_ERROR or 'missing system dependencies'}")
    return HTML(string=html_content or "<p>No content</p>").write_pdf()


def sanitize_topic_for_path(topic: str) -> str:
    """Return a filesystem-friendly version of the topic."""
    cleaned = re.sub(r'[^\w\s-]', '', (topic or 'research')).strip()
    if not cleaned:
        cleaned = 'research'
    cleaned = re.sub(r'[-\s]+', '_', cleaned).lower()
    return cleaned[:50] or 'research'


class InputGuardrails:
    BLOCKED_PATTERNS = [
        r'ignore previous instructions',
        r'you are now',
        r'system prompt',
        r'<script>',
        r'\.\./\.\./\.\./',  # Path traversal
    ]

    SENSITIVE_TOPICS = [
        'how to make explosives',
        'illegal activities',
        'personal data extraction',
    ]

    DEPTH_LEVELS = ["fast", "normal", "deep"]

    def validate_input(self, topic: str, max_length: int = 500) -> dict:
        """Validates and sanitizes user input"""
        if not topic:
            return {"valid": False, "reason": "Topic is required"}

        if len(topic) > max_length:
            return {"valid": False, "reason": "Topic exceeds maximum length"}

        topic_lower = topic.lower()
        for pattern in self.BLOCKED_PATTERNS:
            if re.search(pattern, topic_lower, re.IGNORECASE):
                return {"valid": False, "reason": "Potential prompt injection detected"}

        for sensitive in self.SENSITIVE_TOPICS:
            if sensitive in topic_lower:
                return {"valid": False, "reason": "Topic not permitted", "requires_review": True}

        sanitized = html.escape(topic.strip())
        return {"valid": True, "sanitized_topic": sanitized}

    def validate_request_scope(self, topic: str, depth: str) -> dict:
        """Prevent resource exhaustion attacks"""
        depth_normalized = (depth or "normal").lower()

        if depth_normalized not in self.DEPTH_LEVELS:
            return {"valid": False, "reason": "Invalid depth parameter"}

        estimated_queries = self._estimate_query_count(topic, depth_normalized)
        if estimated_queries > 100:
            return {
                "valid": False,
                "reason": "Topic scope too broad - would generate excessive queries",
                "suggestion": "Please narrow your research topic"
            }

        return {"valid": True, "depth": depth_normalized}

    def _estimate_query_count(self, topic: str, depth: str) -> int:
        """Very rough heuristic based on topic length and depth multiplier"""
        base_queries = max(5, len(topic.split()))
        depth_multiplier = {
            "fast": 1,
            "normal": 3,
            "deep": 6
        }.get(depth, 3)

        return base_queries * depth_multiplier


app = Flask(__name__)
cleanup_old_outputs(OUTPUTS_DIR)
guardrails = InputGuardrails()

# Global state
job_status = "IDLE" 
job_logs = queue.Queue()
latest_research_output = ""
output_file_path = ""
stop_event = threading.Event()


class QueueLogger(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            # Logs going to logging system will eventually hit stdout/stderr 
            # and be handled by GlobalOutputRedirector.
            # But we can also put them in the queue directly if needed.
            # job_logs.put(msg) 
        except Exception:
            self.handleError(record)


def run_research_background(topic, output_dir, depth="normal"):
    global job_status, latest_research_output, output_file_path, stop_event
    base_output_dir = os.path.abspath(output_dir or 'Research')
    safe_topic = sanitize_topic_for_path(topic)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    run_folder_name = f"{safe_topic}_{timestamp}"
    run_output_dir = os.path.join(base_output_dir, run_folder_name)
    os.makedirs(run_output_dir, exist_ok=True)
    logger.info(f"Writing artifacts for this run to: {run_output_dir}")
    
    # Clear persistent memory to avoid embedding conflicts
    for dir_name in ['db', '.crewai', 'chroma']:
        full_path = os.path.join(os.getcwd(), dir_name)
        if os.path.exists(full_path):
            try:
                shutil.rmtree(full_path)
                logger.info(f"Cleared memory directory: {full_path}")
            except Exception as e:
                logger.warning(f"Failed to clear {full_path}: {e}")
        
        # Also check src/research_assistant/dir_name if running from root
        sub_path = os.path.join(os.path.dirname(__file__), dir_name)
        if os.path.exists(sub_path) and sub_path != full_path:
            try:
                shutil.rmtree(sub_path)
                logger.info(f"Cleared memory directory: {sub_path}")
            except Exception as e:
                logger.warning(f"Failed to clear {sub_path}: {e}")

    try:
        job_status = "RUNNING"
        logger.info("Inside try block, initializing Crew...")
        inputs = {'topic': topic, 'current_year': str(time.localtime().tm_year)}

        crew_instance = ResearchAssistant()
        logger.info("Crew initialized. Starting pipeline...")
        
        # Pass stop check callback to pipeline
        result = crew_instance.run_pipeline(
            inputs=inputs, 
            depth=depth,
            stop_check=lambda: stop_event.is_set()
        )
        
        if stop_event.is_set():
             logger.info("Pipeline stopped by user.")
             job_status = "STOPPED"
        else:
             logger.info("Pipeline finished.")
             job_status = "COMPLETED"
             if hasattr(result, 'raw'):
                 latest_research_output = result.raw
             else:
                 latest_research_output = str(result)
             
             filename = f"research_{safe_topic}_{timestamp}.md"
             output_path = os.path.join(run_output_dir, filename)
             output_file_path = os.path.abspath(output_path)
             with open(output_path, 'w', encoding='utf-8') as f:
                 f.write(latest_research_output)
             print(f"\n✅ Research completed! Output saved to: {output_file_path}")
        
    except Exception as e:
        job_status = "FAILED"
        logger.error(f"Detailed error: {e}")
        logger.error(traceback.format_exc())
    finally:
        # No cleanup needed for global redirects
        pass

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stop-research', methods=['POST'])
def stop_research():
    global job_status, stop_event
    if job_status == "RUNNING":
        stop_event.set()
        job_status = "STOPPING"
        sys.stderr.write("🛑 Stop signal received...\n")
        return jsonify({"status": "stopping", "message": "Stopping research..."})
    return jsonify({"status": "ignored", "message": "No active job"})

@app.route('/api/start-research', methods=['POST'])
def start_research():
    global job_status, latest_research_output, stop_event
    
    stop_event.clear() # Reset stop signal
    # ... rest ...
    
    # HTMX sends form data, not JSON usually, unless hx-json-enc used.
    # Default hx-post is form-urlencoded.
    topic = request.form.get('topic')
    output_path = request.form.get('outputPath', 'Research')
    depth = request.form.get('depth_val', 'normal') # hidden input in index.html

    def _guardrail_error(resp_data, status_code=400):
        if request.is_json or request.headers.get('Accept') == 'application/json':
            return jsonify(resp_data), status_code
        return f"<div class='p-4 bg-red-500/10 border border-red-500/50 text-red-500 rounded-lg'>{resp_data.get('message', resp_data.get('reason', 'Invalid request'))}</div>", status_code

    # If already running, return appropriate format
    if job_status == "RUNNING":
        return _guardrail_error({"status": "error", "message": "Capabilities saturated. A job is already active."}, 409)

    is_json_request = request.is_json or request.headers.get('Accept') == 'application/json'

    if is_json_request:
        while not job_logs.empty(): job_logs.get()
        latest_research_output = ""

        if request.is_json:
            data = request.json
            topic = data.get('topic')
            output_path = data.get('outputPath', 'Research')
            depth = data.get('depth', 'normal')

    if not topic:
        logger.error("Start Request missing topic")
        return _guardrail_error({"status": "error", "message": "Topic required"}, 400)

    validation = guardrails.validate_input(topic)
    if not validation.get("valid"):
        logger.warning(f"Topic validation failed: {validation}")
        return _guardrail_error({"status": "error", "message": validation.get("reason", "Invalid topic")}, 400)

    topic = validation["sanitized_topic"]

    scope_validation = guardrails.validate_request_scope(topic, depth)
    if not scope_validation.get("valid"):
        logger.warning(f"Scope validation failed: {scope_validation}")
        body = {
            "status": "error",
            "message": scope_validation.get("reason", "Invalid request")
        }
        suggestion = scope_validation.get("suggestion")
        if suggestion:
            body["suggestion"] = suggestion
        return _guardrail_error(body, 400)

    depth = scope_validation["depth"]

    logger.info(f"Launching thread for topic: {topic}")
    job_status = "RUNNING"
    thread = threading.Thread(target=run_research_background, args=(topic, output_path, depth))
    thread.daemon = True
    thread.start()
    logger.info("Thread started")

    if is_json_request:
        return jsonify({"status": "started", "message": "Research initiated"})
    
    # Return the Active Workspace Fragment (Swaps into #active-view)
    # Using Tailwind classes to match the design
    return f"""
        <!-- Header (Swapped in) -->
        <div class="p-4 border-b border-white/10 flex justify-between items-center bg-[#0B1120]/40">
            <h2 class="text-xs font-bold text-cyan-500 uppercase tracking-widest flex items-center gap-2">
                <span>📡</span> Live Operation Canvas
            </h2>
            <div class="flex gap-2">
                 <span class="text-xs text-slate-400 font-mono self-center">Targeting: {topic}</span>
            </div>
        </div>
        
        <!-- Main Content Area -->
        <div class="flex-1 flex overflow-hidden relative">
            <!-- Content Stream -->
             <div id="report-container" 
                  class="flex-1 p-10 overflow-y-auto prose prose-invert prose-sm max-w-none text-slate-300
                         prose-headings:text-white prose-a:text-indigo-400 prose-code:text-cyan-400 prose-pre:bg-slate-900/50">
                <!-- Initial State -->
                <div class="h-full flex flex-col items-center justify-center text-slate-500 opacity-50 gap-4">
                    <div class="text-4xl animate-pulse">⚛</div>
                    <p>Initializing neural pathways...</p>
                </div>
                
                <!-- Polling for result or SSE update? 
                     User asked for "hx-post... to stream results". 
                     The report is generated at the END.
                     So we can poll for the final result or wait for SSE 'completed' event to trigger a fetch.
                     Let's add an HTMX trigger here that listens to the SSE completion event.
                -->
                <!-- JS Handles Result Fetching -->
                <div id="result-placeholder"></div>
            </div>
            
            <!-- Citation Rail (Optional, could be hidden initially) -->
            <div class="w-64 bg-[#0B1120]/40 border-l border-white/10 p-5 hidden lg:flex flex-col gap-4">
                <h4 class="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Sources</h4>
                <!-- Injected via result fragment later -->
            </div>
        </div>
        
        <script>
            // Simple JS to hide hero view logic if needed, but HTMX swap handles DOM.
            document.getElementById('hero-view').classList.add('hidden');
            document.getElementById('active-view').classList.remove('hidden');
            document.getElementById('sidebar-topic').value = "{topic}";
        </script>
    """

@app.route('/api/events')
def stream_events():
    def generate():
        while True:
            try:
                # 1. Log Streaming
                try:
                    log_chunk = job_logs.get(timeout=1.0)
                    clean_chunk = re.sub(r'\x1b\[[0-9;]*m', '', log_chunk)
                    
                    # Send JSON data for client-side parsing
                    data = json.dumps({"log": clean_chunk})
                    yield f"event: log\ndata: {data}\n\n"
                    
                except queue.Empty:
                    pass

                # 2. Status Streaming
                yield f"event: status\ndata: {job_status}\n\n"

                if job_status in ["COMPLETED", "FAILED"] and job_logs.empty():
                     yield f"event: completed\ndata: done\n\n"
                     break
                     
            except Exception:
                break
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/result-fragment')
def get_result_fragment():
    global latest_research_output
    if job_status == "COMPLETED":
        # Render Markdown to HTML
        raw_text = str(latest_research_output)
        print(f"DEBUG: Rendering Markdown length: {len(raw_text)}")
        print(f"DEBUG: Markdown snippet: {raw_text[:100]}")
        
        html_content = markdown2.markdown(raw_text, extras=['fenced-code-blocks', 'tables', 'break-on-newline'])
        return html_content
    elif job_status == "FAILED":
        return "<div class='text-red-400'>Research failed. Check logs.</div>"
    else:
        return "..." # Keep waiting

@app.route('/api/download-report', methods=['GET'])
def download_report():
    global job_status, output_file_path
    if job_status != "COMPLETED":
        return jsonify({"error": "No completed report available"}), 400

    format_param = (request.args.get('format') or 'markdown').lower()
    if format_param not in {"markdown", "html", "pdf"}:
        return jsonify({"error": "Unsupported format"}), 400

    markdown_text = _load_latest_markdown()
    if not markdown_text:
        return jsonify({"error": "No report content available"}), 404

    try:
        if format_param == "markdown":
            filename = os.path.basename(output_file_path or "research_report.md")
            if not filename.endswith(".md"):
                filename = "research_report.md"
            return send_file(
                io.BytesIO(markdown_text.encode('utf-8')),
                as_attachment=True,
                download_name=filename,
                mimetype='text/markdown'
            )

        html_content = _render_markdown_to_html(markdown_text)
        if format_param == "html":
            filename = os.path.splitext(os.path.basename(output_file_path or "research_report"))[0] + ".html"
            return send_file(
                io.BytesIO(html_content.encode('utf-8')),
                as_attachment=True,
                download_name=filename,
                mimetype='text/html'
            )

        # PDF
        pdf_bytes = _render_pdf_from_html(html_content)
        filename = os.path.splitext(os.path.basename(output_file_path or "research_report"))[0] + ".pdf"
        return send_file(
            io.BytesIO(pdf_bytes),
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )

    except Exception as exc:
        logger.error(f"Error preparing download ({format_param}): {exc}")
        return jsonify({"error": "Failed to generate requested format"}), 500

if __name__ == '__main__':
    print("🚀 Starting Research Agent on http://localhost:5000")
    app.run(debug=False, host='0.0.0.0', port=5000)
