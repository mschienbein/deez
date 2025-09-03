#!/usr/bin/env python3
"""
Docker service management tools for Deez Music Agent
"""

import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result"""
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def start_services():
    """Start all Docker services"""
    print("🚀 Starting Deez Music Agent services...")
    result = run_command(["docker-compose", "up", "-d"])
    if result.returncode == 0:
        print("✅ Services started successfully")
        print("\nService URLs:")
        print("  Neo4j Browser: http://localhost:7474 (neo4j/deezmusic123)")
        print("  slskd UI: http://localhost:5030")
        print("  MinIO Console: http://localhost:9001 (minioadmin/minioadmin123)")
    else:
        print(f"❌ Failed to start services: {result.stderr}")
        sys.exit(1)


def stop_services():
    """Stop all Docker services"""
    print("🛑 Stopping Deez Music Agent services...")
    result = run_command(["docker-compose", "down"])
    if result.returncode == 0:
        print("✅ Services stopped successfully")
    else:
        print(f"❌ Failed to stop services: {result.stderr}")
        sys.exit(1)


def show_logs(service: str = None):
    """Show Docker logs"""
    cmd = ["docker-compose", "logs", "-f"]
    if service:
        cmd.append(service)
    
    print(f"📋 Showing logs{f' for {service}' if service else ''}...")
    print("Press Ctrl+C to exit")
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n✅ Exiting log view")


def check_status():
    """Check service status"""
    print("🔍 Checking service status...\n")
    result = run_command(["docker-compose", "ps"])
    print(result.stdout)
    
    # Check specific services
    services = ["neo4j", "postgres", "slskd", "redis", "minio"]
    all_healthy = True
    
    for service in services:
        container_name = f"deez-{service}"
        result = run_command(
            ["docker", "inspect", "--format='{{.State.Status}}'", container_name],
            check=False
        )
        
        if result.returncode == 0:
            status = result.stdout.strip().strip("'")
            if status == "running":
                print(f"✅ {service:10} - Running")
            else:
                print(f"⚠️  {service:10} - {status}")
                all_healthy = False
        else:
            print(f"❌ {service:10} - Not found")
            all_healthy = False
    
    if all_healthy:
        print("\n✅ All services are healthy")
    else:
        print("\n⚠️  Some services need attention")


def restart_service(service: str):
    """Restart a specific service"""
    print(f"🔄 Restarting {service}...")
    result = run_command(["docker-compose", "restart", service])
    if result.returncode == 0:
        print(f"✅ {service} restarted successfully")
    else:
        print(f"❌ Failed to restart {service}: {result.stderr}")
        sys.exit(1)


def clean_volumes():
    """Clean up Docker volumes"""
    print("🧹 Cleaning up Docker volumes...")
    print("⚠️  WARNING: This will delete all data!")
    
    response = input("Are you sure? (yes/no): ")
    if response.lower() != "yes":
        print("❌ Cancelled")
        return
    
    run_command(["docker-compose", "down", "-v"])
    print("✅ Volumes cleaned")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python docker_tools.py [start|stop|logs|status|restart|clean]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "start":
        start_services()
    elif command == "stop":
        stop_services()
    elif command == "logs":
        service = sys.argv[2] if len(sys.argv) > 2 else None
        show_logs(service)
    elif command == "status":
        check_status()
    elif command == "restart":
        if len(sys.argv) < 3:
            print("Usage: python docker_tools.py restart <service>")
            sys.exit(1)
        restart_service(sys.argv[2])
    elif command == "clean":
        clean_volumes()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()