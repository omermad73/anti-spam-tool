#!/usr/bin/env python3
"""
Simple complaint dashboard server for Anti Spam extension

Listens on port 8787 and provides:
- GET / : Dashboard UI with complaint list and counter
- POST /complaint : Receive complaints
- POST /reset : Clear all complaints
- GET /status : JSON status for live updates
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import sys

HOST = '127.0.0.1'
PORT = 8787

# In-memory storage
complaints_log = []


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Anti Spam Complaint Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            padding: 40px;
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        
        .counter-box {
            background: #f0f4ff;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-bottom: 30px;
            border-radius: 5px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .counter-info {
            font-size: 14px;
            color: #666;
        }
        
        .counter-number {
            font-size: 36px;
            font-weight: bold;
            color: #667eea;
        }
        
        .complaints-section {
            margin-bottom: 20px;
        }
        
        .complaints-section h2 {
            color: #333;
            font-size: 18px;
            margin-bottom: 10px;
        }
        
        #complaintLog {
            width: 100%;
            height: 300px;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 13px;
            background: #f9f9f9;
            resize: vertical;
            color: #333;
            overflow-y: auto;
        }
        
        .button-group {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        
        button {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .btn-reset {
            background: #ff6b6b;
            color: white;
        }
        
        .btn-reset:hover {
            background: #ee5a52;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(255, 107, 107, 0.3);
        }
        
        .btn-refresh {
            background: #667eea;
            color: white;
        }
        
        .btn-refresh:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
        }
        
        .status {
            margin-top: 15px;
            font-size: 12px;
            color: #999;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Complaint Dashboard</h1>
        <p class="subtitle">Real-time spam complaint tracking</p>
        
        <div class="counter-box">
            <div>
                <div class="counter-info">Total Complaints Received</div>
                <div class="counter-number" id="counter">0</div>
            </div>
            <div style="color: #999; font-size: 12px;">
                Auto-updating every 1 second
            </div>
        </div>
        
        <div class="complaints-section">
            <h2>Complaint Log</h2>
            <textarea id="complaintLog" readonly></textarea>
        </div>
        
        <div class="button-group">
            <button class="btn-reset" onclick="resetComplaints()">Clear All Complaints</button>
            <button class="btn-refresh" onclick="refreshStatus()">Refresh Now</button>
        </div>
        
        <div class="status">
            <span id="lastUpdate">Last updated: never</span>
        </div>
    </div>

    <script>
        // Poll for updates every 1 second
        setInterval(refreshStatus, 1000);
        
        // Initial load
        refreshStatus();
        
        function refreshStatus() {
            fetch('/status')
                .then(res => res.json())
                .then(data => {
                    document.getElementById('counter').textContent = data.count;
                    document.getElementById('complaintLog').value = data.log.join('\\n');
                    // Scroll to bottom
                    const textarea = document.getElementById('complaintLog');
                    textarea.scrollTop = textarea.scrollHeight;
                    document.getElementById('lastUpdate').textContent = 
                        'Last updated: ' + new Date().toLocaleTimeString();
                })
                .catch(err => console.error('Status fetch error:', err));
        }
        
        function resetComplaints() {
            if (confirm('Are you sure you want to clear all complaints?')) {
                fetch('/reset', { method: 'POST' })
                    .then(res => res.json())
                    .then(data => {
                        if (data.ok) {
                            refreshStatus();
                        }
                    })
                    .catch(err => console.error('Reset error:', err));
            }
        }
    </script>
</body>
</html>"""


class ComplaintHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode('utf-8'))
            return
        
        if self.path == '/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                'count': len(complaints_log),
                'log': complaints_log
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
            return
        
        self.send_response(404)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"ok": false, "error": "not_found"}')

    def do_POST(self):
        if self.path == '/complaint':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length) if length > 0 else b''
            complaint_text = body.decode('utf-8', errors='replace')
            
            # Add to log
            complaints_log.append(complaint_text)
            print(f'Complaint received: {complaint_text}')
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
            return
        
        if self.path == '/reset':
            complaints_log.clear()
            print('Complaints cleared')
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
            return
        
        self.send_response(404)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"ok": false, "error": "not_found"}')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        sys.stdout.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format%args))


def run(server_class=HTTPServer, handler_class=ComplaintHandler):
    server_address = (HOST, PORT)
    httpd = server_class(server_address, handler_class)
    print(f"Anti Spam Complaint Dashboard starting at http://{HOST}:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down')
        httpd.server_close()


if __name__ == '__main__':
    run()
