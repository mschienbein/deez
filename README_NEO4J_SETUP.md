# Neo4j & Graphiti Setup for Deez Music Agent

## Quick Start

1. **Install Dependencies**
   ```bash
   uv pip install -e .
   ```

2. **Start Services**
   ```bash
   uv run up
   # or
   docker-compose up -d
   ```

3. **Initialize Databases**
   ```bash
   uv run init-db
   # or
   uv run python scripts/init_databases.py
   ```

3. **Access Services**
   - Neo4j Browser: http://localhost:7474 (neo4j/deezmusic123)
   - slskd UI: http://localhost:5030
   - MinIO Console: http://localhost:9001 (minioadmin/minioadmin123)

## Architecture Overview

The music agent uses a hybrid database architecture:

### Neo4j + Graphiti (Relationships & Memory)
- Temporal knowledge graph for conversation history
- Music relationships (similar tracks, mixes well with)
- User preferences and listening patterns
- Discovery context and sources

### PostgreSQL (Factual Data)
- Track metadata (title, artist, BPM, key)
- Platform identifiers (Spotify, Deezer, etc.)
- Rekordbox database mirror
- Download history

## Key Components

### 1. MusicMemory Class (`src/music_agent/integrations/graphiti_memory.py`)
Main interface for Graphiti operations:
- `add_conversation()` - Store chat interactions
- `add_track_discovery()` - Record discovered tracks
- `add_preference()` - Track user preferences
- `search_memory()` - Query the knowledge graph

### 2. Music Ontologies (`src/music_agent/models/ontologies.py`)
Pydantic models defining entities and relationships:
- Core: Track, Artist, Album, Genre, Playlist
- DJ: CuePoint, BeatGrid, Loop, DJFolder
- P2P: P2PSource, DownloadSource
- Preferences: ListeningSession, MusicPreference

### 3. Database Schema (`infrastructure/postgres/init/01_schema.sql`)
PostgreSQL tables for factual data:
- music.tracks, artists, albums, genres
- rekordbox.tracks, cue_points, beat_grids
- music.download_sources, p2p_sources

## Common Commands with UV

```bash
# Service Management
uv run up               # Start all Docker services
uv run down             # Stop all Docker services
uv run logs             # View Docker logs
uv run status           # Check service status

# Database Operations
uv run init-db          # Initialize databases
uv run neo4j-shell      # Open Cypher shell
uv run postgres-shell   # Open psql shell
uv run neo4j-status     # Check Neo4j connection
uv run postgres-status  # Check PostgreSQL connection
uv run rekordbox-sync   # Sync with Rekordbox database

# Development
uv run test             # Run tests
uv run lint             # Run linting
uv run format           # Format code
uv run typecheck        # Type checking with mypy
uv run clean            # Clean build artifacts

# Service UIs
uv run neo4j-browser    # Open Neo4j browser
uv run slskd-ui         # Open slskd UI
uv run minio-console    # Open MinIO console

# Main CLI
uv run deez             # Run the music agent CLI
```

### Direct Python Script Usage

You can also run scripts directly:

```bash
# Docker management
uv run python scripts/docker_tools.py start
uv run python scripts/docker_tools.py logs neo4j
uv run python scripts/docker_tools.py restart postgres

# Database tools
uv run python scripts/database_tools.py backup-neo4j
uv run python scripts/database_tools.py backup-postgres

# Development tools
uv run python scripts/dev_tools.py check-all
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Core
OPENAI_API_KEY=your-key

# Neo4j (Graphiti)
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=deezmusic123

# PostgreSQL
POSTGRES_PASSWORD=music123

# Services
SLSKD_USERNAME=your-soulseek-user
SPOTIFY_CLIENT_ID=your-spotify-id
DEEZER_ARL=your-deezer-arl
```

## Testing the Setup

1. **Check Neo4j Connection**
   ```python
   from src.music_agent.integrations.graphiti_memory import MusicMemory
   import asyncio
   
   async def test():
       memory = MusicMemory()
       await memory.initialize()
       print("✅ Connected to Neo4j")
   
   asyncio.run(test())
   ```

2. **Query Neo4j**
   ```cypher
   # In Neo4j Browser or cypher-shell
   MATCH (n) RETURN count(n) as node_count;
   MATCH ()-[r]->() RETURN count(r) as relationship_count;
   ```

3. **Check PostgreSQL**
   ```sql
   -- In psql
   \dt music.*
   SELECT count(*) FROM music.tracks;
   ```

## Troubleshooting

### Neo4j Connection Issues
- Ensure Docker is running: `docker ps`
- Check Neo4j logs: `uv run logs neo4j`
- Check connection: `uv run neo4j-status`
- Verify credentials in `.env`

### Graphiti Import Errors
- Install graphiti-core: `pip install graphiti-core`
- Check OpenAI API key is set

### PostgreSQL Schema Missing
- Run migrations: `uv run init-db`
- Check postgres logs: `uv run logs postgres`
- Check connection: `uv run postgres-status`

## Next Steps

1. **Sync Rekordbox**: `uv run rekordbox-sync`
2. **Configure slskd**: Add Soulseek credentials in `.env`
3. **Test music discovery**: `uv run deez`
4. **Monitor memory**: `uv run neo4j-browser` to explore the graph

## UV Command Reference

All commands are defined in `pyproject.toml` under `[project.scripts]` and `[tool.uv.aliases]`.

### Adding New Commands

To add a new command, edit `pyproject.toml`:

```toml
[project.scripts]
my-command = "module.path:function"

# or for aliases
[tool.uv.aliases]
my-alias = "python scripts/my_script.py"
```

Then run with: `uv run my-command` or `uv run my-alias`