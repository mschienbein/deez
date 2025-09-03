#!/usr/bin/env python3
"""
Database management tools for Deez Music Agent
"""

import subprocess
import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def neo4j_shell():
    """Open Neo4j cypher shell"""
    print("🔷 Opening Neo4j Cypher Shell...")
    print("Login: neo4j / deezmusic123")
    print("Example queries:")
    print("  MATCH (n) RETURN count(n);")
    print("  MATCH ()-[r]->() RETURN count(r);")
    print("  MATCH (n:Episode) RETURN n LIMIT 10;")
    print("Type :exit to quit\n")
    
    subprocess.run([
        "docker", "exec", "-it", "deez-neo4j",
        "cypher-shell", "-u", "neo4j", "-p", "deezmusic123"
    ])


def postgres_shell():
    """Open PostgreSQL shell"""
    print("🐘 Opening PostgreSQL Shell...")
    print("Database: music_catalog")
    print("Example queries:")
    print("  \\dt music.*")
    print("  SELECT count(*) FROM music.tracks;")
    print("  \\q to quit\n")
    
    subprocess.run([
        "docker", "exec", "-it", "deez-postgres",
        "psql", "-U", "music_agent", "-d", "music_catalog"
    ])


async def check_neo4j():
    """Check Neo4j connection and status"""
    print("🔷 Checking Neo4j status...")
    
    try:
        from src.music_agent.integrations.graphiti_memory import MusicMemory
        
        memory = MusicMemory()
        await memory.initialize()
        
        # Get some stats
        query = """
        MATCH (n) 
        WITH labels(n) as label_list
        UNWIND label_list as label
        RETURN label, count(*) as count
        ORDER BY count DESC
        """
        
        results = await memory.graphiti.driver.execute_query(query)
        
        print("✅ Neo4j connected successfully\n")
        print("Node counts by label:")
        for record in results:
            print(f"  {record['label']:20} {record['count']:>10}")
        
        await memory.close()
        
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        sys.exit(1)


async def check_postgres():
    """Check PostgreSQL connection and status"""
    print("🐘 Checking PostgreSQL status...")
    
    try:
        import asyncpg
        
        conn = await asyncpg.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            user=os.getenv("POSTGRES_USER", "music_agent"),
            password=os.getenv("POSTGRES_PASSWORD", "music123"),
            database=os.getenv("POSTGRES_DB", "music_catalog")
        )
        
        # Get version
        version = await conn.fetchval("SELECT version()")
        print(f"✅ PostgreSQL connected: {version.split(',')[0]}\n")
        
        # Get table counts
        query = """
        SELECT 
            schemaname,
            tablename,
            n_live_tup as row_count
        FROM pg_stat_user_tables
        WHERE schemaname IN ('music', 'rekordbox')
        ORDER BY schemaname, tablename;
        """
        
        results = await conn.fetch(query)
        
        if results:
            print("Table row counts:")
            current_schema = None
            for row in results:
                if row['schemaname'] != current_schema:
                    current_schema = row['schemaname']
                    print(f"\n  {current_schema}:")
                print(f"    {row['tablename']:20} {row['row_count']:>10}")
        else:
            print("No tables found in music or rekordbox schemas")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        sys.exit(1)


def backup_neo4j():
    """Backup Neo4j database"""
    from datetime import datetime
    
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_name = f"neo4j-{timestamp}"
    
    print(f"📦 Backing up Neo4j to {backup_name}...")
    
    # Create backup in container
    result = subprocess.run([
        "docker", "exec", "deez-neo4j",
        "neo4j-admin", "database", "dump", "music",
        "--to-path=/data/backups"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        # Copy backup to local
        subprocess.run([
            "docker", "cp",
            "deez-neo4j:/data/backups",
            f"backups/{backup_name}"
        ])
        print(f"✅ Neo4j backed up to backups/{backup_name}")
    else:
        print(f"❌ Backup failed: {result.stderr}")
        sys.exit(1)


def backup_postgres():
    """Backup PostgreSQL database"""
    from datetime import datetime
    
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_file = backup_dir / f"postgres-{timestamp}.sql"
    
    print(f"📦 Backing up PostgreSQL to {backup_file}...")
    
    with open(backup_file, "w") as f:
        result = subprocess.run([
            "docker", "exec", "deez-postgres",
            "pg_dump", "-U", "music_agent", "music_catalog"
        ], stdout=f, stderr=subprocess.PIPE, text=True)
    
    if result.returncode == 0:
        print(f"✅ PostgreSQL backed up to {backup_file}")
    else:
        print(f"❌ Backup failed: {result.stderr}")
        backup_file.unlink()
        sys.exit(1)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python database_tools.py [neo4j-shell|postgres-shell|neo4j-status|postgres-status|backup-neo4j|backup-postgres]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "neo4j-shell":
        neo4j_shell()
    elif command == "postgres-shell":
        postgres_shell()
    elif command == "neo4j-status":
        asyncio.run(check_neo4j())
    elif command == "postgres-status":
        asyncio.run(check_postgres())
    elif command == "backup-neo4j":
        backup_neo4j()
    elif command == "backup-postgres":
        backup_postgres()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()