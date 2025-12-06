from flask import Flask, render_template, request, jsonify, Response, send_file
import threading
import queue
import time
import os
import sys
import io
import json
import re
from research_assistant.crew import ResearchAssistant

app = Flask(__name__)

# Global state for simplicity in this local-user app
job_status = "IDLE" # IDLE, RUNNING, COMPLETED, FAILED
job_logs = queue.Queue()
latest_research_output = ""
output_file_path = ""

class LogCapture(io.StringIO):
    def write(self, data):
        job_logs.put(data)
        sys.__stdout__.write(data) # Also write to real stdout

def run_research_background(topic, output_dir):
    global job_status, latest_research_output, output_file_path
    job_status = "RUNNING"
    
    # Capture stdout
    original_stdout = sys.stdout
    sys.stdout = LogCapture()
    
    try:
        inputs = {
            'topic': topic,
            'current_year': str(time.localtime().tm_year)
        }
        
        # Ensure output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # We need to tell the crew where to write the final file.
        # Currently crew.py writes to hardcoded paths or what's in tasks.yaml.
        # For this MVP, we'll let it run as configured, but we can capture the result.
        
        # Initialize and run
        crew_instance = ResearchAssistant()
        result = crew_instance.run_pipeline(inputs=inputs)
        
        latest_research_output = str(result)
        
        # Attempt to find the file
        # The publisher task writes to "Research/final_research.md" by default
        # We can try to copy it or just point to it.
        default_path = os.path.join("Research", "final_research.md")
        if os.path.exists(default_path):
            output_file_path = os.path.abspath(default_path)
            
        job_status = "COMPLETED"
        print(f"\n✅ Research completed! Output saved to: {output_file_path}")
        
    except Exception as e:
        job_status = "FAILED"
        print(f"\n❌ detailed error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        sys.stdout = original_stdout

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/research', methods=['POST'])
def start_research():
    global job_status
    if job_status == "RUNNING":
        return jsonify({"status": "error", "message": "A job is already running."}), 400
        
    data = request.json
    topic = data.get('topic')
    output_path = data.get('outputPath', 'Research')
    
    if not topic:
        return jsonify({"status": "error", "message": "Topic is required."}), 400

    # clear logs
    while not job_logs.empty():
        job_logs.get()
        
    thread = threading.Thread(target=run_research_background, args=(topic, output_path))
    thread.daemon = True
    thread.start()
    
    return jsonify({"status": "started"})

@app.route('/api/status')
def stream_status():
    def generate():
        while True:
            try:
                # Non-blocking get
                log_chunk = job_logs.get(timeout=1.0)
                
                # 1. Strip ANSI color codes
                clean_chunk = re.sub(r'\x1b\[[0-9;]*m', '', log_chunk)
                
                # 2. Filter logic
                msg_to_send = None
                
                # Priority 1: Custom Status Messages
                if "✨" in clean_chunk:
                    msg_to_send = clean_chunk
                    
                # Priority 2: Extract Titles from raw JSON output (e.g. "title": "...")
                # We look for the pattern "title": "Something"
                elif '"title":' in clean_chunk:
                    match = re.search(r'"title":\s*"(.*?)"', clean_chunk)
                    if match:
                        title = match.group(1)
                        # Avoid duplicates or junk
                        if len(title) > 5:
                            msg_to_send = f"🔍 Found resource: {title}\n"

                # Priority 3: Errors
                elif "❌" in clean_chunk or "Error" in clean_chunk:
                    msg_to_send = clean_chunk

                if msg_to_send:
                     yield f"data: {json.dumps({'log': msg_to_send, 'status': job_status})}\n\n"
                    
            except queue.Empty:
                # Send keepalive event with just status
                yield f"data: {json.dumps({'status': job_status})}\n\n"
                if job_status in ["COMPLETED", "FAILED"] and job_logs.empty():
                    break
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/result')
def get_result():
    global latest_research_output, output_file_path
    
    content = ""
    if output_file_path and os.path.exists(output_file_path):
         with open(output_file_path, 'r', encoding='utf-8') as f:
             content = f.read()
    elif latest_research_output:
        content = latest_research_output
        
    return jsonify({
        "status": job_status,
        "markdown": content,
        "downloadUrl": "/api/download" if output_file_path else None
    })

@app.route('/api/download')
def download_file():
    global output_file_path
    if output_file_path and os.path.exists(output_file_path):
        return send_file(output_file_path, as_attachment=True)
    return "File not found", 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
