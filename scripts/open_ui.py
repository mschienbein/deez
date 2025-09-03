#!/usr/bin/env python3
"""
Open service UIs in browser
"""

import sys
import webbrowser
import platform


def open_neo4j():
    """Open Neo4j browser"""
    url = "http://localhost:7474"
    print(f"🔷 Opening Neo4j Browser at {url}")
    print("Login: neo4j / deezmusic123")
    webbrowser.open(url)


def open_slskd():
    """Open slskd web UI"""
    url = "http://localhost:5030"
    print(f"🎵 Opening slskd UI at {url}")
    webbrowser.open(url)


def open_minio():
    """Open MinIO console"""
    url = "http://localhost:9001"
    print(f"📦 Opening MinIO Console at {url}")
    print("Login: minioadmin / minioadmin123")
    webbrowser.open(url)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python open_ui.py [neo4j|slskd|minio]")
        sys.exit(1)
    
    service = sys.argv[1]
    
    if service == "neo4j":
        open_neo4j()
    elif service == "slskd":
        open_slskd()
    elif service == "minio":
        open_minio()
    else:
        print(f"Unknown service: {service}")
        print("Available services: neo4j, slskd, minio")
        sys.exit(1)


if __name__ == "__main__":
    main()