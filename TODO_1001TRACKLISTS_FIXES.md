# TODO: 1001 Tracklists Integration Fixes

## Current Status
- ✅ All functions implemented
- ✅ Playwright integrated for JavaScript rendering  
- ❌ HTML parsers don't match current site structure

## Non-Working Tools That Need Fixes

### 1. `search_tracklists` 
- Returns empty results
- Need to update HTML selectors for search results
- File: `src/music_agent/integrations/tracklists_simple.py:432-557`

### 2. `get_dj_recent_sets`
- Returns empty results  
- Depends on search function
- DJ profile URLs return 404
- File: `src/music_agent/integrations/tracklists_simple.py:559-673`

### 3. `get_festival_tracklists`
- Returns empty results
- Festival URLs return 404
- File: `src/music_agent/integrations/tracklists_simple.py:675-818`

## Required Actions

### Step 1: Analyze Current HTML Structure
- [ ] Use Playwright to save actual HTML from 1001 Tracklists
- [ ] Identify correct selectors for tracks, artists, titles
- [ ] Find working URL patterns for DJ profiles and festivals

### Step 2: Update Parsers
- [ ] Update `_extract_tracks()` with correct selectors
- [ ] Fix search result parsing
- [ ] Update DJ profile URL construction
- [ ] Fix festival page parsing

### Step 3: Alternative Approach
- [ ] Consider intercepting API calls instead of HTML parsing
- [ ] Use Playwright's native selectors instead of BeautifulSoup
- [ ] Add playwright-stealth for better anti-bot evasion

## Files to Modify
- `src/music_agent/integrations/tracklists_simple.py`
- `src/music_agent/tools/tracklists_simple_tools.py` (if needed)

## Testing
- Use `scripts/test_tracklists_comprehensive.py` to verify fixes
- Test with real 1001 Tracklists URLs once selectors are updated

## Note
The architecture is solid - just needs HTML selector updates to match current site structure. All data processing functions work correctly.