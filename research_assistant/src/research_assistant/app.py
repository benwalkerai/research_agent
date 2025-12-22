from flask import Flask, render_template, request, jsonify, Response, send_file
import threading
import queue
import time
import os
import sys
import io
import json
import re
from dotenv import load_dotenv
import markdown2
from research_assistant.crew import ResearchAssistant
import traceback
import shutil

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

app = Flask(__name__)

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
        if not os.path.exists(output_dir): os.makedirs(output_dir)

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
             
             # Generate unique filename from topic and timestamp
             import re
             from datetime import datetime
             safe_topic = re.sub(r'[^\w\s-]', '', topic).strip()[:50]  # Remove special chars, limit length
             safe_topic = re.sub(r'[-\s]+', '_', safe_topic).lower()   # Replace spaces/dashes with underscores
             timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
             filename = f"research_{safe_topic}_{timestamp}.md"
             
             output_path = os.path.join(output_dir, filename)
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

    # If already running, return appropriate format
    if job_status == "RUNNING":
        if request.is_json or request.headers.get('Accept') == 'application/json':
            return jsonify({"status": "error", "message": "Capabilities saturated. A job is already active."}), 409
        return """<div class="p-4 bg-red-500/10 border border-red-500/50 text-red-500 rounded-lg">
                    Capabilities saturated. A job is already active.
                   </div>""", 409

    # Support JSON for JS client
    if request.is_json or request.headers.get('Accept') == 'application/json':
        # Reset state
        while not job_logs.empty(): job_logs.get()
        latest_research_output = ""
        
        # main.js sends JSON body: JSON.stringify({ topic, outputPath, depth })
        if request.is_json:
            data = request.json
            topic = data.get('topic')
            output_path = data.get('outputPath', 'Research')
            depth = data.get('depth', 'normal')
        
        if not topic:
            logger.error("Start Request missing topic")
            return jsonify({"status": "error", "message": "Topic required"}), 400
            
        logger.info(f"Launching thread for topic: {topic}")
        job_status = "RUNNING"  # [UPDATE] Set status immediately
        thread = threading.Thread(target=run_research_background, args=(topic, output_path, depth))
        thread.daemon = True
        thread.start()
        logger.info("Thread started")
        
        return jsonify({"status": "started", "message": "Research initiated"})
    
    # HTMX / Form fallback
    if job_status == "RUNNING":
         return """<div class="p-4 bg-red-500/10 border border-red-500/50 text-red-500 rounded-lg">
                    Capabilities saturated. A job is already active.
                   </div>"""
    
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

@app.route('/api/download-report')
def download_report():
    """Download the generated research report as a markdown file."""
    global output_file_path, job_status
    
    if job_status != "COMPLETED":
        return jsonify({"error": "No completed research available"}), 404
    
    if not output_file_path or not os.path.exists(output_file_path):
        return jsonify({"error": "Report file not found"}), 404
    
    try:
        return send_file(
            output_file_path,
            as_attachment=True,
            download_name='research_report.md',
            mimetype='text/markdown'
        )
    except Exception as e:
        return jsonify({"error": f"Failed to download file: {str(e)}"}), 500

if __name__ == '__main__':
    print("🚀 Starting Research Agent on http://localhost:5000")
    app.run(debug=False, host='0.0.0.0', port=5000)
