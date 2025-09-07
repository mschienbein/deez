# 💎 Quality & Acquisition Strategy

## 6. **Quality & Acquisition**

#### Quality Definition
**What defines "high quality" for you?**
- [ ] Lossless only (FLAC/WAV/AIFF)
- [ ] 320kbps MP3 acceptable
- [ ] 256kbps AAC acceptable
- [x] Quality varies by use case
- [ ] Other: _______________

**Quality Priorities:**
```
1. Scale-based system (0-100)
2. No minimum threshold - everything has a score
3. Higher quality always preferred when available
```

#### Purchase Preferences
**Platform Priority for Purchasing**
- [x] Beatport (electronic focus)
- [x] Bandcamp (artist support)
- [ ] iTunes/Apple Music
- [ ] Amazon Music
- [x] Direct from label
- [ ] Other: _______________

**Budget Considerations:**
```
- No automation for purchases (manual only)
- Collect metadata about source for future purchase
- Store purchase links when available
- Track where files originated from
```

#### Region-Locked Content
- [ ] Use VPN/proxy
- [ ] Skip region-locked
- [x] Find alternative sources
- [ ] Manual intervention

**Strategy:**
```
- Not a major concern for our use case
- Try alternative sources automatically
- Agent handles region issues transparently
```

#### Download Automation
- [ ] Just provide links
- [ ] Auto-purchase from Beatport
- [x] Download from streaming (where legal)
- [x] Queue downloads for manual review
- [x] Full automation with rules

**Automation Rules:**
```
- Show top 5 matches ranked by:
  1. Quality score (0-100)
  2. Metadata accuracy match
  3. Source priority (Soulseek > Deezer > Spotify > YouTube)
- Soulseek as de facto choice (most accurate for obscure/remixes)
- Compare all sources before final selection
- Handle edge cases (weird filenames, obscure remixes)
- Allow user override when agent makes mistakes
```

---

## 🎵 Quality Standards

### Audio Quality Tiers
**Quality Scale System (0-100):**

```
100 - FLAC 24-bit/96kHz+
95  - FLAC 24-bit/48kHz
90  - FLAC 16-bit/44.1kHz (CD Quality)
85  - WAV 16-bit/44.1kHz
80  - ALAC (Apple Lossless)
75  - 320 kbps MP3/AAC
70  - 256 kbps MP3/AAC
65  - 192 kbps MP3/AAC
60  - 160 kbps MP3/AAC
55  - 128 kbps MP3/AAC
50  - 96 kbps MP3/AAC
40  - 64 kbps MP3/AAC
30  - < 64 kbps
20  - Streaming rip (unknown quality)
10  - Poor quality/corrupted
0   - Unplayable/invalid
```

**Notes:**
- No minimum threshold - all tracks get a quality score
- Quality is the only factor (no source differentiation)
- Agents make decisions based on quality scores
- Version selection (radio/extended/remix) handled by agent context

---

## 📥 Acquisition Workflow

### Search Priority
**Order of source checking:**
```
1. Soulseek (rare/high quality files)
2. Deezer (mainstream catalog)
3. Spotify (comprehensive catalog)
4. Beatport (electronic music metadata)
5. YouTube (last resort/playlists)
```

### Decision Tree
```
If found on Soulseek at 320kbps+ → Download
Else if found on Deezer → Download
Else if found on Spotify → Download
Else if found on YouTube at decent quality → Download
Else → Mark for manual review
```

**Agent-Based Decision Making:**
```
- AcquisitionScout searches all sources in parallel
- QualityAssessor scores each result (0-100)
- Agent selects highest quality score
- If multiple versions exist (radio/extended/remix):
  → Agent interprets user intent from context
  → Selects appropriate version
- No quality is "unacceptable" - everything gets scored
```

### Quality Verification
- [x] Check file headers
- [ ] Analyze spectrum
- [x] Compare file sizes
- [ ] Listen test samples
- [ ] Trust source
- [ ] Other: _______________

**Verification Process:**
```
1. Quick header check (< 1 second) for format/bitrate
2. Size validation (flag if significantly off expected)
3. Full verification only if suspicious
```

---

## 💰 Purchase Strategy

### Auto-Purchase Rules
**When to automatically buy:**
- [ ] Never auto-purchase
- [ ] If under $X
- [ ] If from preferred labels
- [ ] If marked as "must have"
- [ ] Other: _______________

**Conditions:**
```
- Price limit: $_____
- Preferred stores: _______________
- Preferred labels: _______________
- 
```

### Manual Review Queue
**Tracks requiring review:**
- [ ] Above price threshold
- [ ] Multiple versions available
- [ ] Quality concerns
- [ ] Rare/exclusive releases
- [ ] Other: _______________

**Review Interface:**
```
- Show: _______________
- Compare: _______________
- Actions: _______________
```

---

## 🔄 Replacement Strategy

### Existing Library Upgrades
**When to replace existing tracks:**
- [ ] Always if higher quality found
- [ ] Only if significantly better (define: _______)
- [x] Manual approval required
- [ ] Never auto-replace
- [ ] Other: _______________

**Quality Improvement Process:**
```
1. Check if track exists in main PostgreSQL database
2. Compare with Rekordbox database alignment
3. Evaluate current quality score and metadata completeness
4. Flag tracks that could be improved (not highest quality)
5. Provide tool to search flagged tracks for upgrades
6. Queue all upgrades for human approval
7. Track search history to avoid repeated searches
```

### Backup Policy
- [x] Keep original versions
- [ ] Archive replaced tracks
- [ ] Delete after confirmation
- [ ] Other: _______________

**Backup Strategy:**
```
- Keep originals until user confirms replacement
- Store in designated backup folder
- Clean up after successful replacement
```

---

## 📊 Source Reliability

### Platform Trust Levels
**All sources treated equally:**
```
- Quality score is the only metric
- No source bias or trust levels
- Verification based on file analysis, not source
- All platforms can provide good or bad quality
```

### Verification Requirements
**Universal verification approach:**
```
- All files get same verification regardless of source
- Quick header check for all files
- Full verification only when suspicious:
  - File size mismatch
  - Header inconsistencies
  - Corrupted data indicators
```

---

## 🎯 Special Cases

### Rare/Exclusive Tracks
**Handling unavailable tracks:**
- [ ] Accept lower quality
- [x] Mark for future search
- [ ] Request from community
- [ ] Purchase at any price
- [x] Other: Track search history

**Strategy:**
```
- Same quality standards as normal tracks
- After first search with no improvements, flag as "hard to find"
- Track search history to avoid repeated searches
- Some tracks may never have better versions (e.g., 320 is best available)
- Provide option for library-wide re-search of flagged tracks
```

### Bootlegs/Edits
**Quality expectations:**
- [ ] Accept any quality
- [ ] Minimum threshold: _____
- [ ] Skip if below standard
- [x] Other: Same standards as regular tracks

**Handling:**
```
- Apply same quality scoring system (0-100)
- Flag as "hard to find better" after unsuccessful search
- Track that best available version has been found
```

### Live Recordings
**Acceptable quality:**
```
- No minimum bitrate - use quality scale
- Audience recording: Acceptable (lower score)
- Soundboard required: No (but higher score)
- Same standards as studio recordings
```

---

## 📈 Quality Metrics

### Track Success Criteria
**A successfully acquired track has:**
- [ ] Correct metadata
- [ ] Acceptable quality
- [ ] Proper file format
- [ ] Album art
- [ ] Verified authenticity
- [ ] Other: _______________

### Library Quality Goals
```
- Track quality improvements over time
- Identify tracks flagged for potential upgrade
- Monitor "hard to find" tracks for future availability
- Maintain search history to avoid redundant searches
```

### Monitoring
- [ ] Quality reports
- [ ] Upgrade suggestions
- [ ] Library statistics
- [ ] Other: _______________

**Report Frequency:**
```
- 
- 
```

---

## ⚖️ Legal & Ethical Considerations

### Content Sources
**Acceptable sources:**
- [ ] Purchased content only
- [x] Legal streaming rips
- [ ] P2P for owned content
- [x] P2P for unavailable content
- [ ] Other: _______________

**Policy:**
```
- Use all available sources to find best quality
- Store download links when available
- Track source metadata for future purchase options
```

### Rights Management
- [ ] Track ownership
- [ ] License compliance
- [ ] DMCA compliance
- [ ] Other: _______________

**Approach:**
```
- 
- 
- 
```

---

## ❓ Open Questions

1. How to handle multiple versions (radio edit, extended, remix)?
   → Agent interprets user intent from context
2. Should we analyze actual audio quality or trust metadata?
   → Quick header check, full analysis only if suspicious
3. How to detect fake high-bitrate files?
   → File size validation + header consistency check
4. What about DJ edits and transitions?
   → Treat same as any track, quality score applies
5. How to handle compilation vs. original release?
   → Agent preference based on context
6. Should we support vinyl rips?
   → Yes, score based on quality like any other source
7. How to verify Soulseek sources?
   → Same verification as all sources (no trust bias)
8. 
9. 
10.