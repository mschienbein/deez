# LLM Service & 1001 Tracklists Integration

## Summary of Implementation

### 1. General LLM Service ✅

Created a reusable LLM service (`src/music_agent/services/llm_service.py`) with:

- **Multiple model support** - GPT-5 as default (as requested)
- **Structured data extraction** with Pydantic schemas
- **Automatic retries** with exponential backoff
- **Token usage tracking**
- **Multiple response formats** (text, JSON, structured)
- **Classification and analysis helpers**
- **Embedding generation**
- **Content moderation**

#### Key Features

```python
# Quick completion
response = await quick_complete("Analyze this track: ...")

# Structured extraction
from pydantic import BaseModel
class TrackInfo(BaseModel):
    artist: str
    title: str
    genre: str

track = await quick_extract(text, TrackInfo)

# Analysis
analysis = await service.analyze(
    data=tracklist,
    analysis_type="dj_style",
    instructions="Identify mixing patterns and genre preferences"
)

# Classification
genre = await service.classify(
    text="Dark driving techno with acid elements",
    categories=["Techno", "House", "Trance", "Drum & Bass"]
)
```

### 2. 1001 Tracklists Integration ✅

Created an efficient scraper (`src/music_agent/integrations/tracklists_simple.py`) that:

- **Returns raw structured data** for agent processing (as you suggested)
- **No LLM overhead** during extraction
- **Pattern-based parsing** for reliability
- **Built-in caching** (1-hour TTL)
- **Rate limiting** (2 seconds between requests)
- **Browser-like headers** to avoid blocking

#### Data Structure Returned

```python
{
    "url": "https://www.1001tracklists.com/...",
    "title": "Carl Cox @ Space Ibiza",
    "dj": "Carl Cox",
    "event": "Music Is Revolution Closing",
    "date": "2016-09-20",
    "genres": ["Techno", "Tech House"],
    "tracks": [
        {
            "position": 1,
            "cue": "00:00",
            "artist": "Carl Cox",
            "title": "Space Calling",
            "remix": null,
            "label": "Intec",
            "mix_type": null,
            "is_id": false
        },
        ...
    ],
    "recording_links": {
        "soundcloud": "https://soundcloud.com/...",
        "mixcloud": "https://mixcloud.com/..."
    },
    "stats": {
        "views": 50000,
        "favorites": 1200
    }
}
```

### 3. Agent Tools ✅

Created 9 simple tools (`src/music_agent/tools/tracklists_simple_tools.py`):

1. **`get_tracklist(url)`** - Fetch raw tracklist data
2. **`search_tracklists(query)`** - Search for tracks/DJs
3. **`get_dj_recent_sets(dj_name)`** - Get DJ's recent performances
4. **`get_festival_tracklists(url)`** - Get all sets from a festival
5. **`extract_track_list(data)`** - Clean track list extraction
6. **`get_tracklist_stats(data)`** - Statistics summary
7. **`find_common_tracks(urls)`** - Find tracks across multiple sets
8. **`analyze_tracklist_progression(data)`** - Basic set structure analysis
9. **`export_as_playlist(data)`** - Export as formatted text

## Architecture Decision

### Why Simple Scraping + Agent Processing

As you suggested, the implementation:

1. **Returns plain data** - The scraper just extracts structured data
2. **Agent handles intelligence** - The LLM service can analyze the data when needed
3. **Efficient pipeline** - No LLM calls during extraction = faster and cheaper
4. **Flexible processing** - Agent can decide how to interpret data

### Data Flow

```
1001TL Website → BeautifulSoup Parser → Structured JSON → Agent Tools → LLM Analysis (optional)
                         ↓                      ↓                              ↑
                  (Pattern matching)      (Raw data)                    (When needed)
```

## Usage Examples

### Basic Tracklist Fetching
```python
# Get tracklist data
data = get_tracklist("https://www.1001tracklists.com/...")

# Agent can process raw data
tracks = extract_track_list(data)
stats = get_tracklist_stats(data)

# Only use LLM when needed for analysis
if user_wants_analysis:
    analysis = await llm_service.analyze(
        data=data,
        analysis_type="set_progression",
        instructions="Analyze the energy flow and mixing style"
    )
```

### Finding Common Tracks
```python
# Get data from multiple sets
urls = [festival_set1, festival_set2, festival_set3]
common = find_common_tracks(urls)

# Most played tracks (no LLM needed)
top_tracks = {k: v for k, v in common.items() if v > 2}
```

### LLM Analysis When Needed
```python
# Agent decides to use LLM for deeper analysis
tracklist_data = get_tracklist(url)

# Use LLM service for intelligent analysis
service = get_llm_service()
insights = await service.analyze(
    data=tracklist_data,
    analysis_type="dj_style",
    instructions="""
    Based on this tracklist:
    1. Identify the mixing style (harmonic, energy-based, etc.)
    2. Determine the genre progression
    3. Find the peak time section
    4. Suggest similar DJs
    """,
    return_json=True
)
```

## Benefits of This Approach

1. **Performance** - No unnecessary LLM calls
2. **Cost-effective** - LLM only when adding value
3. **Reliable** - Pattern matching for extraction
4. **Flexible** - Agent controls processing
5. **Cacheable** - Raw data can be cached easily
6. **Testable** - Clear separation of concerns

## Configuration

Set in `.env`:
```bash
# For LLM Service
OPENAI_API_KEY="your-key"
OPENAI_MODEL="gpt-5"  # Default model

# No config needed for tracklists scraping
```

## Testing

Run the test script:
```bash
uv run python scripts/test_tracklists.py
```

This will:
- Test tracklist extraction (with mock data if URL fails)
- Verify LLM service initialization
- Save output to `tracklist_test_output.json`

## Next Steps

The integration is complete and ready for use. The agent can:

1. **Fetch tracklists** and return structured data
2. **Process the data** without LLM overhead
3. **Use LLM service** when intelligent analysis is needed
4. **Cache results** to minimize scraping

The separation between data extraction and LLM processing makes the system efficient and cost-effective, exactly as you envisioned.