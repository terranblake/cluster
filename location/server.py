#!/usr/bin/env python3
"""
GPS Tracker Server
Simple Flask server for tracking GPS locations from log files
"""

import os
import json
import glob
from datetime import datetime, timedelta
from flask import Flask, jsonify, send_from_directory

app = Flask(__name__, static_folder='static')

# Configuration
LOG_DIR = os.environ.get('LOG_DIR', '/logs')
PORT = int(os.environ.get('PORT', 8080))
ONE_MONTH_IN_HOURS = 30 * 24
MAX_AGE_HOURS = int(os.environ.get('MAX_AGE_HOURS', ONE_MONTH_IN_HOURS))

def parse_logs():
    """Parse all GPS log files and return recent locations"""
    locations = []
    cutoff_time = datetime.now() - timedelta(hours=MAX_AGE_HOURS)
    log_files = glob.glob(os.path.join(LOG_DIR, '*.log'))
    
    for log_file in log_files:
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split(',')
                    if len(parts) < 4:
                        print(f"Skipping malformed line in {log_file}: {line}")
                        continue
                    
                    timestamp_str = parts[0]
                    device_id = parts[1]
                    lat = float(parts[2])
                    lon = float(parts[3])
                    accuracy = float(parts[4]) if len(parts) > 4 else 0
                    
                    # Parse timestamp
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        if timestamp.tzinfo:
                            timestamp = timestamp.replace(tzinfo=None)
                    except:
                        continue
                    
                    # Only include recent locations
                    if timestamp <= cutoff_time:
                        locations.append({
                            'timestamp': timestamp.isoformat(),
                            'device_id': device_id,
                            'lat': lat,
                            'lon': lon,
                            'accuracy': accuracy
                        })
        except Exception as e:
            print(f"Error reading {log_file}: {e}")
    
    # Sort by timestamp
    locations.sort(key=lambda x: x['timestamp'])
    return locations

def get_latest_locations():
    """Get the most recent location for each device"""
    all_locations = parse_logs()
    latest = {}
    
    for loc in all_locations:
        device_id = loc['device_id']
        if device_id not in latest or loc['timestamp'] > latest[device_id]['timestamp']:
            latest[device_id] = loc
    
    return list(latest.values())

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('static/html', 'index.html')

@app.route('/api/locations')
def api_locations():
    """API endpoint to get all recent locations"""
    return jsonify(parse_logs())

@app.route('/api/latest')
def api_latest():
    """API endpoint to get latest location per device"""
    return jsonify(get_latest_locations())

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'log_dir': LOG_DIR})

# Static file routes
@app.route('/css/<path:filename>')
def css_files(filename):
    return send_from_directory('static/css', filename)

@app.route('/js/<path:filename>')
def js_files(filename):
    return send_from_directory('static/js', filename)

if __name__ == '__main__':
    # Ensure log directory exists
    os.makedirs(LOG_DIR, exist_ok=True)
    print(f"Starting GPS map server on port {PORT}")
    print(f"Reading logs from: {LOG_DIR}")
    print(f"Max age for locations: {MAX_AGE_HOURS} hours")
    app.run(host='0.0.0.0', port=PORT, debug=False)