#!/usr/bin/env python3
"""
Simple HTTP server for development testing of Telegram WebApp
"""

import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

# Configuration
PORT = 8080
DIRECTORY = Path(__file__).parent

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)

    def end_headers(self):
        # Add CORS headers for development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def log_message(self, format, *args):
        # Custom logging
        print(f"[{self.date_time_string()}] {format % args}")

def main():
    try:
        with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
            print(f"Starting development server...")
            print(f"WebApp URL: http://localhost:{PORT}")
            print(f"Serving from: {DIRECTORY}")
            print(f"Open in browser: http://localhost:{PORT}")
            print(f"\nPress Ctrl+C to stop the server\n")

            # Open browser automatically
            # webbrowser.open(f'http://localhost:{PORT}')

            httpd.serve_forever()

    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"Error: Port {PORT} is already in use")
            print(f"Try a different port or stop the existing server")
        else:
            print(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()