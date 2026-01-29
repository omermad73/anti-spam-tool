#!/usr/bin/env python3
"""
Simple local test server for Anti Spam extension

Provides two endpoints used by the extension during development:
- POST /check   -> accepts JSON {"urls": [ ... ]} and returns JSON results per-URL
- POST /report  -> accepts a spam report JSON and returns acknowledgement
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
import sys
import re
import os
import hashlib

HOST = '127.0.0.1'
PORT = 3000
BAD_URLS_FILE = os.path.join(os.path.dirname(__file__), 'bad_urls.json')
MEMBERS_FILE = os.path.join(os.path.dirname(__file__), 'members.json')


def load_bad_urls():
    """Load bad URLs from persistent storage"""
    if not os.path.exists(BAD_URLS_FILE):
        return set()
    try:
        with open(BAD_URLS_FILE, 'r') as f:
            data = json.load(f)
            return set(data) if isinstance(data, list) else set()
    except Exception as e:
        print(f"Error loading bad URLs: {e}")
        return set()


def save_bad_urls(bad_urls):
    """Save bad URLs to persistent storage"""
    try:
        with open(BAD_URLS_FILE, 'w') as f:
            json.dump(sorted(list(bad_urls)), f, indent=2)
    except Exception as e:
        print(f"Error saving bad URLs: {e}")


def extract_urls(text):
    """Extract URLs from text using regex"""
    if not isinstance(text, str):
        return []
    # Match http/https URLs
    pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    return re.findall(pattern, text)


def hash_email(email):
    """Hash an email address using SHA256"""
    if not isinstance(email, str):
        return None
    email_lower = email.strip().lower()
    return hashlib.sha256(email_lower.encode()).hexdigest()


def load_members():
    """Load hashed member emails from persistent storage"""
    if not os.path.exists(MEMBERS_FILE):
        return set()
    try:
        with open(MEMBERS_FILE, 'r') as f:
            data = json.load(f)
            return set(data) if isinstance(data, list) else set()
    except Exception as e:
        print(f"Error loading members: {e}")
        return set()


def save_members(members):
    """Save hashed member emails to persistent storage"""
    try:
        with open(MEMBERS_FILE, 'w') as f:
            json.dump(sorted(list(members)), f, indent=2)
    except Exception as e:
        print(f"Error saving members: {e}")


class SimpleHandler(BaseHTTPRequestHandler):
    def _set_cors_headers(self, status=200, content_type='application/json'):
        self.send_response(status)
        # Allow extension to call this server from browser
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Type', content_type)
        self.end_headers()

    def do_OPTIONS(self):
        self._set_cors_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        
        if parsed.path == '/filter':
            # Serve the filter HTML page
            try:
                html_path = os.path.join(os.path.dirname(__file__), 'filter.html')
                with open(html_path, 'r') as f:
                    html_content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html_content.encode('utf-8'))
                return
            except Exception as e:
                print(f"Error serving filter.html: {e}")
                self.send_response(500)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Error loading page')
                return
        
        # Unknown endpoint
        self.send_response(404)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Not found')

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        
        if parsed.path == '/filter-emails':
            resp = self.handle_filter_emails()
            self._set_cors_headers(200)
            self.wfile.write(json.dumps(resp).encode('utf-8'))
            return
        
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length) if length > 0 else b''
        try:
            data = json.loads(body.decode('utf-8')) if body else {}
        except Exception:
            data = {}

        if parsed.path == '/check':
            print('POST /check received:', data)
            resp = self.handle_check(data)
            self._set_cors_headers(200)
            self.wfile.write(json.dumps(resp).encode('utf-8'))
            return

        if parsed.path == '/report':
            print('POST /report received:', data)
            resp = self.handle_report(data)
            self._set_cors_headers(200)
            self.wfile.write(json.dumps(resp).encode('utf-8'))
            return

        # Unknown endpoint
        self._set_cors_headers(404)
        self.wfile.write(json.dumps({'ok': False, 'error': 'not_found'}).encode('utf-8'))

    def handle_check(self, data):
        # Expecting { "urls": [ ... ], "email": "..." }
        urls = data.get('urls') if isinstance(data, dict) else None
        email = data.get('email') if isinstance(data, dict) else None
        
        if not isinstance(urls, list):
            return {'ok': False, 'error': 'invalid_payload', 'results': []}

        # Hash and store email if provided
        if email:
            hashed_email = hash_email(email)
            if hashed_email:
                members = load_members()
                if hashed_email not in members:
                    members.add(hashed_email)
                    save_members(members)
                    print(f"New member added: {hashed_email}")

        bad_urls = load_bad_urls()
        results = []
        for u in urls:
            try:
                url_str = str(u).strip()
                # Return only URLs that exist in the bad URL list
                is_bad = url_str in bad_urls
                results.append({'url': url_str, 'spam': is_bad})
            except Exception:
                results.append({'url': u, 'spam': False})

        return {
            'ok': True,
            'results': results
        }

    def handle_report(self, data):
        # Extract URLs from the report payload and add to bad list
        bad_urls = load_bad_urls()
        
        # Extract URLs from various fields that might contain them
        urls_found = []
        
        # Check if data has a urls field (direct list)
        if isinstance(data.get('urls'), list):
            urls_found.extend(data.get('urls', []))
        
        # Extract URLs from string fields in the payload
        if isinstance(data, dict):
            for value in data.values():
                if isinstance(value, str):
                    urls_found.extend(extract_urls(value))
        
        # Add new URLs to the bad list (avoid duplicates)
        added_count = 0
        for url in urls_found:
            url_str = str(url).strip()
            if url_str and url_str not in bad_urls:
                bad_urls.add(url_str)
                added_count += 1
        
        # Save updated list
        if added_count > 0:
            save_bad_urls(bad_urls)
        
        return {'ok': True, 'received': True, 'added': added_count, 'payload': data}

    def handle_filter_emails(self):
        """Handle email list filtering by parsing multipart form data"""
        try:
            # Parse multipart form data
            content_type = self.headers.get('Content-Type', '')
            if not content_type.startswith('multipart/form-data'):
                return {'ok': False, 'error': 'Expected multipart/form-data'}
            
            # Extract boundary
            boundary = None
            for part in content_type.split(';'):
                if 'boundary=' in part:
                    boundary = part.split('boundary=')[1].strip()
                    break
            
            if not boundary:
                return {'ok': False, 'error': 'No boundary found'}
            
            # Read body
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            
            # Parse multipart data manually (simple approach)
            parts = body.split(('--' + boundary).encode())
            file_content = None
            
            for part in parts:
                if b'filename=' in part and b'Content-Type: application/json' in part:
                    # Extract file content
                    lines = part.split(b'\r\n\r\n', 1)
                    if len(lines) == 2:
                        file_content = lines[1].strip()
                        # Remove trailing boundary markers
                        file_content = file_content.rstrip(b'\r\n--')
                        break
            
            if not file_content:
                return {'ok': False, 'error': 'No JSON file found in upload'}
            
            # Parse JSON
            try:
                uploaded_emails = json.loads(file_content.decode('utf-8'))
            except Exception as e:
                return {'ok': False, 'error': f'Invalid JSON: {str(e)}'}
            
            if not isinstance(uploaded_emails, list):
                return {'ok': False, 'error': 'JSON must be an array of emails'}
            
            # Load existing members (SHA256 hashes)
            members_hashes = load_members()
            
            # Filter out members
            filtered_emails = []
            members_found = 0
            
            for email in uploaded_emails:
                if not isinstance(email, str):
                    continue
                
                email_hash = hash_email(email)
                if email_hash and email_hash in members_hashes:
                    members_found += 1
                else:
                    filtered_emails.append(email)
            
            return {
                'ok': True,
                'original': uploaded_emails,
                'filtered': filtered_emails,
                'original_count': len(uploaded_emails),
                'members_count': members_found,
                'filtered_count': len(filtered_emails)
            }
            
        except Exception as e:
            print(f"Error in handle_filter_emails: {e}")
            return {'ok': False, 'error': str(e)}

    def log_message(self, format, *args):
        # Log to stdout
        sys.stdout.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format%args))


def run(server_class=HTTPServer, handler_class=SimpleHandler):
    server_address = (HOST, PORT)
    httpd = server_class(server_address, handler_class)
    print(f"Starting test server at http://{HOST}:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down')
        httpd.server_close()


if __name__ == '__main__':
    run()
