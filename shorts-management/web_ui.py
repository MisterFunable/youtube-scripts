#!/usr/bin/env python3
"""
YouTube Shorts Processing Web UI
Simple web interface to manage video processing
"""

import os
import json
import subprocess
import threading
import time
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
import psutil

# Add parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)

# Configuration
VIDEOS_FILE = "videos_today.json"
PROCESSED_FILE = "processed.json"
QUEUE_FILE = "video_queue.json"
SHORTS_UPDATER = "shorts_updater.py"

# Set OpenAI API key from environment
if os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

class ProcessingManager:
    def __init__(self):
        self.current_process = None
        self.processing_log = []
        self.is_processing = False
    
    def start_processing(self, limit=None, dry_run=False):
        if self.is_processing:
            return False, "Already processing"
        
        cmd = ["python3", SHORTS_UPDATER, "--input", VIDEOS_FILE]
        if limit:
            cmd.extend(["--limit", str(limit)])
        if dry_run:
            cmd.append("--dry-run")
        
        self.is_processing = True
        self.processing_log = []
        
        def run_process():
            try:
                # Set environment variables for the subprocess
                env = os.environ.copy()
                if os.getenv("OPENAI_API_KEY"):
                    env["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
                
                # Set PYTHONPATH to include parent directory
                python_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                if "PYTHONPATH" in env:
                    env["PYTHONPATH"] = f"{python_path}:{env['PYTHONPATH']}"
                else:
                    env["PYTHONPATH"] = python_path
                
                process = subprocess.Popen(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    env=env,
                    cwd=os.getcwd()  # Ensure we're in the right directory
                )
                self.current_process = process
                
                for line in process.stdout:
                    self.processing_log.append({
                        'timestamp': datetime.now().isoformat(),
                        'message': line.strip()
                    })
                
                process.wait()
                self.is_processing = False
                self.current_process = None
                
            except Exception as e:
                self.processing_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'message': f"Error: {str(e)}"
                })
                self.is_processing = False
                self.current_process = None
        
        thread = threading.Thread(target=run_process)
        thread.daemon = True
        thread.start()
        
        return True, "Processing started"
    
    def stop_processing(self):
        if self.current_process:
            self.current_process.terminate()
            self.is_processing = False
            return True, "Processing stopped"
        return False, "No process running"
    
    def get_status(self):
        return {
            'is_processing': self.is_processing,
            'log': self.processing_log[-50:] if self.processing_log else []  # Last 50 lines
        }

manager = ProcessingManager()

def get_video_stats():
    """Get statistics about videos"""
    stats = {
        'total_videos': 0,
        'processed_videos': 0,
        'queue_videos': 0
    }
    
    # Count videos in main file
    if os.path.exists(VIDEOS_FILE):
        try:
            with open(VIDEOS_FILE, 'r') as f:
                videos = json.load(f)
                stats['total_videos'] = len(videos)
        except:
            pass
    
    # Count processed videos
    if os.path.exists(PROCESSED_FILE):
        try:
            with open(PROCESSED_FILE, 'r') as f:
                processed = json.load(f)
                stats['processed_videos'] = len(processed)
        except:
            pass
    
    # Count queue videos
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, 'r') as f:
                queue = json.load(f)
                stats['queue_videos'] = len(queue)
        except:
            pass
    
    return stats

@app.route('/')
def index():
    stats = get_video_stats()
    status = manager.get_status()
    # Pass datetime to the template
    return render_template('index.html', 
                         stats=stats, 
                         status=status, 
                         datetime=datetime)

@app.route('/api/start', methods=['POST'])
def start_processing():
    data = request.get_json()
    limit = data.get('limit')
    dry_run = data.get('dry_run', False)
    
    success, message = manager.start_processing(limit, dry_run)
    return jsonify({'success': success, 'message': message})

@app.route('/api/stop', methods=['POST'])
def stop_processing():
    success, message = manager.stop_processing()
    return jsonify({'success': success, 'message': message})

@app.route('/api/status')
def get_processing_status():
    return jsonify(manager.get_status())

@app.route('/api/resume', methods=['POST'])
def resume_from():
    data = request.get_json()
    start_index = data.get('start_index', 0)
    
    try:
        if os.path.exists(VIDEOS_FILE):
            with open(VIDEOS_FILE, 'r') as f:
                videos = json.load(f)
            
            if start_index >= len(videos):
                return jsonify({'success': False, 'message': 'Start index exceeds video count'})
            
            # Keep only videos from start_index onward
            remaining_videos = videos[start_index:]
            
            with open(VIDEOS_FILE, 'w') as f:
                json.dump(remaining_videos, f, indent=2, ensure_ascii=False)
            
            return jsonify({
                'success': True, 
                'message': f'Resumed from video {start_index + 1}. {len(remaining_videos)} videos remaining.'
            })
        else:
            return jsonify({'success': False, 'message': 'Videos file not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/stats')
def get_stats():
    return jsonify(get_video_stats())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
