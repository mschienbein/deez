# 🎮 DJ Software Integration

## Primary DJ Software
- [x] Rekordbox only
- [ ] Also Traktor
- [ ] Also Serato
- [ ] Virtual DJ
- [ ] Other: _______________

**Version Information:**
```
- Software: Rekordbox
- Version: 7.2.0
- OS: macOS
```

## Export Requirements
- [x] Hot cues must transfer
- [x] Memory cues needed
- [x] Loops important
- [x] Beat grid critical
- [x] Comments/tags
- [x] Other: Color tags, MyTags, Related tracks

**Priority Order:**
```
1. Beat grid/BPM (essential for mixing)
2. Hot cues (performance critical)
3. Memory cues & loops
4. Tags/comments/colors
```

## Library Management
- [ ] Rekordbox is master library
- [ ] Separate tool manages library
- [x] Multiple libraries synced
- [x] Other: Profile-based isolation

**Multi-Profile Architecture:**
```
1. Profile Management
   - Default profile (auto-loads main Rekordbox)
   - Guest/Friend mode (temporary, isolated)
   - Event profiles (gigs, parties)
   
2. Database Structure:
   - Master tables (all tracks, metadata, sources)
   - Profile sub-tables (track selections, playlists)
   - Shared file storage (no duplicates)
   - Profile-specific Rekordbox sync
   
3. File Storage:
   - Single master pool of audio files
   - Profiles reference same files
   - Different profiles can push different subsets to Rekordbox
   - Prevents library contamination
```

---

## 🎚️ Rekordbox-Specific Features

### Database Integration
**Using pyrekordbox package:**
```python
# Key features to leverage
- Database reading/writing
- Playlist management
- Cue point handling
- Beat grid data
- Key/BPM analysis results
- Color tags
- MyTags
- Related tracks
```

**Profile-Based Features:**
```
- Profile switching command (e.g., --profile guest)
- Backup/restore profiles with cue data
- Export profile as package (for sharing)
- Prevent main library contamination
- Quick friend/guest mode for temporary use
```

### Data Sync Strategy
- [ ] One-way: Our DB → Rekordbox
- [ ] One-way: Rekordbox → Our DB
- [x] Two-way sync
- [x] Selective sync
- [ ] Other: _______________

**Sync Workflow:**
```
1. Initial Import (first run):
   - Pull entire Rekordbox database
   - Create PostgreSQL mirror
   - Store as "profile baseline"
   
2. Regular Operations:
   - Check Rekordbox for changes
   - Pull updates (cues, tags, etc)
   - Push new tracks with metadata
   - Conflict resolution rules
   
3. Conflict Resolution:
   - Rekordbox wins for DJ data (cues, grids)
   - Our DB wins for metadata (quality, source)
   - User prompt for title/artist conflicts
```

**Sync Fields:**
```
Always sync:
- Title, Artist, Album
- BPM, Key
- Genre, Label
- File location
- Date added

Rekordbox → Our DB only:
- Hot cues, Memory cues
- Beat grid
- Play count, last played
- Color tags, MyTags
- Related tracks

Our DB → Rekordbox only:
- Quality score
- Source platform
- Download date
- Alternative versions

Never sync:
- Internal IDs
- Temporary analysis data
```

### Playlist Management
- [x] Import Rekordbox playlists
- [x] Export to Rekordbox playlists
- [ ] Sync playlist changes
- [ ] Create smart playlists
- [ ] Other: _______________

**Playlist Types:**
```
- Regular playlists
- Smart playlists
- History playlists
- 
```

---

## 🎯 Cue Points & Markers

### Cue Point Types
**Priority for preservation:**
- [x] Hot cues (A-H)
- [x] Memory cues
- [x] Loop points
- [x] Beat jump markers
- [ ] Other: _______________

**Handling Strategy:**
```
When upgrading/replacing tracks:
1. Always attempt to preserve existing cues
2. Check for length/timing conflicts
3. If conflict detected:
   - Trust Rekordbox data
   - Flag for manual review
4. Always create backup before changes
5. Store cue backup in database
```

### Beat Grid Management
- [x] Trust Rekordbox analysis
- [ ] Verify with our analysis
- [x] Always preserve existing
- [ ] Update if confidence high
- [ ] Other: _______________

**Beat Grid Policy:**
```
- Rekordbox is authoritative for beat grids
- Preserve grids when upgrading tracks
- Only update if track length changes significantly
- Backup grid data before any changes
```

---

## 🏷️ Tagging & Organization

### Rekordbox Tags
**MyTag usage:**
```
Tag 1: _______________
Tag 2: _______________
Tag 3: _______________
Tag 4: _______________
```

### Color Coding
**Color meanings:**
```
Red: _______________
Orange: _______________
Yellow: _______________
Green: _______________
Aqua: _______________
Blue: _______________
Purple: _______________
Pink: _______________
```

### Rating System
**Rating criteria:**
```
5 stars: _______________
4 stars: _______________
3 stars: _______________
2 stars: _______________
1 star: _______________
```

---

## 📁 File Management

### File Organization
**Master download folder:**
```
/MusicAgent/
  /Downloads/
    /Artist Name/
      Artist - Track Title.mp3
      Artist - Track Title (Remix).mp3
```

**Benefits:**
```
- Single folder to backup/copy
- Human-readable organization
- Easy to migrate to new computer
- Follows Rekordbox-like structure
- No genre/album complexity
```

### File Naming Convention
- [x] Artist - Title
- [x] Artist - Title (Remix)
- [ ] Track# - Artist - Title
- [ ] Custom: _______________

**Format:**
```
Pattern: _______________
Example: _______________
```

### Duplicate Handling
- [ ] Keep both versions
- [x] Replace with higher quality
- [x] Move old to archive
- [ ] Delete duplicates
- [ ] Other: _______________

**Detection Method:**
```
1. Agent-based matching:
   - Compare artist, title, version, remix
   - Check duration (within ~10 seconds)
   - Compare BPM/key if available
   - ISRC/catalog number matching

2. Archive Strategy:
   - Move lower quality to /Archive folder
   - Not synced to Rekordbox
   - Store in archive_tracks table
   - Track upgrade history (old → new)
   - Keep for rollback if needed
```

---

## 🔄 Import/Export Workflows

### Import from Rekordbox
```
1. Read Rekordbox database via pyrekordbox
2. Extract all tracks with metadata
3. Import cues, loops, grids, tags
4. Store in PostgreSQL master tables
5. Mark quality scores for upgrade checks
6. Create baseline snapshot
```

### Export to Rekordbox
```
1. Agent prompts: "Ready to sync to Rekordbox?"
2. Generate sync report (what's being added)
3. User approval required
4. Write to Rekordbox DB via pyrekordbox
5. Report success/failures
6. Update sync timestamp
```

### XML Bridge
**Using Rekordbox XML:**
- [ ] Full library export/import
- [ ] Playlist exchange only
- [ ] Track metadata only
- [x] Not using XML
- [x] Other: Direct DB via pyrekordbox

**Direct Database Benefits:**
```
- Faster than XML parsing
- Real-time sync possible
- Access to all Rekordbox features
- No export/import steps
```

---

## 🎵 Track Analysis

### Analysis Data Sources
- [x] Use Rekordbox analysis
- [x] Use our own analysis
- [x] Merge both results
- [x] Platform-specific (Beatport for electronic)
- [x] Other: Essentia with EDM profiles

**Analysis Strategy:**
```
1. New tracks → Essentia analysis (fast, pre-import)
   - Use EDM-specific profiles ('edma'/'edmm')
   - ~70% accuracy (matches Rekordbox)
2. Store Essentia + platform metadata
3. Import to Rekordbox → let it analyze too
4. Compare results, flag major discrepancies
5. Rekordbox is final authority for DJ performance
```

### Key Detection
**Key notation preference:**
- [ ] Musical (Am, C#)
- [x] Camelot (1A, 8B)
- [ ] Open Key (1m, 8d)
- [x] All formats stored
- [ ] Other: _______________

**Key Analysis Implementation:**
```
1. Primary: Essentia with EDM profiles
   - 'edma' profile for electronic music
   - ~70% accuracy (matches Rekordbox)
2. Secondary: Beatport metadata (if available)
3. Store all notations, display Camelot
4. Rekordbox final authority after import
```

### BPM Analysis
**BPM handling:**
- [x] Trust first source
- [ ] Average multiple sources
- [x] Detect half/double time
- [ ] Manual verification
- [ ] Other: _______________

**Analysis Priority:**
```
1. Rekordbox (if exists)
2. Beatport (most accurate for electronic)
3. librosa.beat.tempo (open source)
4. Platform metadata

Half-time Detection:
- D&B/Dubstep: Often 140-180 (actually 70-90)
- Trap/Hip-Hop: Often shows as 140-160 (actually 70-80)
- Flag for manual review when uncertain
```

---

## 🔗 Related Tracks

### Similarity Matching
**Find related tracks by:**
- [ ] BPM range (±5%)
- [ ] Key compatibility
- [ ] Genre
- [ ] Energy level
- [ ] Year/era
- [ ] Other: _______________

**Matching Algorithm:**
```
- 
- 
- 
```

### Recommendation Engine
- [ ] Based on play history
- [ ] Based on ratings
- [ ] Based on harmonic mixing
- [ ] Based on energy flow
- [ ] Other: _______________

**Recommendation Rules:**
```
- 
- 
- 
```

---

## 📊 Performance Data

### Track Performance Metrics
**Data to track:**
- [ ] Play count
- [ ] Last played
- [ ] Crowd response
- [ ] Mix compatibility
- [ ] Other: _______________

**Storage:**
```
- In Rekordbox: _______________
- In our DB: _______________
- In Graphiti: _______________
```

### Set History
- [ ] Import from Rekordbox history
- [ ] Track successful combinations
- [ ] Note problematic transitions
- [ ] Export set lists
- [ ] Other: _______________

**History Analysis:**
```
- 
- 
- 
```

---

## ⚙️ Advanced Features

### Smart Playlists
**Criteria examples:**
```
- Recently added + High energy + 124-128 BPM
- Never played + 4+ stars + House genre
- 
- 
```

### Intelligent Crates
**Auto-organization rules:**
```
- 
- 
- 
```

### Preparation Tools
**Pre-gig checklist:**
- [ ] Verify all files exist
- [ ] Check audio quality
- [ ] Analyze un-analyzed tracks
- [ ] Export to USB
- [ ] Other: _______________

**Automation:**
```
- 
- 
- 
```

---

## ❓ Integration Questions

1. Should we support CDJ USB export directly?
2. How to handle Rekordbox Cloud sync?
3. Should we integrate with KUVO?
4. Support for DVS (Digital Vinyl System)?
5. How to handle video files?
6. Should we support lighting data?
7. Integration with Rekordbox mobile?
8. Support for multiple Rekordbox versions?
9. 
10.