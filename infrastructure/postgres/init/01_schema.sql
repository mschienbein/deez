-- Music Catalog Database Schema
-- PostgreSQL schema for factual music data

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS music;
CREATE SCHEMA IF NOT EXISTS rekordbox;

-- Set search path
SET search_path TO music, rekordbox, public;

-- ====================================
-- Core Music Tables
-- ====================================

-- Artists table
CREATE TABLE IF NOT EXISTS music.artists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    sort_name VARCHAR(255),
    founded_year INTEGER,
    origin_country VARCHAR(100),
    spotify_id VARCHAR(100) UNIQUE,
    deezer_id VARCHAR(100) UNIQUE,
    discogs_id VARCHAR(100) UNIQUE,
    beatport_id VARCHAR(100) UNIQUE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_artists_name ON music.artists USING gin(name gin_trgm_ops);
CREATE INDEX idx_artists_spotify ON music.artists(spotify_id);
CREATE INDEX idx_artists_deezer ON music.artists(deezer_id);

-- Albums table
CREATE TABLE IF NOT EXISTS music.albums (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    artist_id UUID REFERENCES music.artists(id),
    release_date DATE,
    label VARCHAR(255),
    total_tracks INTEGER,
    album_type VARCHAR(50),
    upc VARCHAR(50) UNIQUE,
    spotify_id VARCHAR(100) UNIQUE,
    deezer_id VARCHAR(100) UNIQUE,
    discogs_id VARCHAR(100) UNIQUE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_albums_title ON music.albums USING gin(title gin_trgm_ops);
CREATE INDEX idx_albums_artist ON music.albums(artist_id);
CREATE INDEX idx_albums_release ON music.albums(release_date);

-- Tracks table
CREATE TABLE IF NOT EXISTS music.tracks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    artist_id UUID REFERENCES music.artists(id),
    album_id UUID REFERENCES music.albums(id),
    duration_ms INTEGER,
    isrc VARCHAR(50) UNIQUE,
    audio_fingerprint VARCHAR(100),
    
    -- Technical metadata
    file_size BIGINT,
    file_type VARCHAR(10),
    bitrate INTEGER,
    sample_rate INTEGER,
    
    -- Musical metadata
    bpm DECIMAL(5,2),
    key VARCHAR(10),
    energy DECIMAL(3,2),
    danceability DECIMAL(3,2),
    
    -- Platform IDs
    spotify_id VARCHAR(100) UNIQUE,
    deezer_id VARCHAR(100) UNIQUE,
    beatport_id VARCHAR(100) UNIQUE,
    discogs_id VARCHAR(100) UNIQUE,
    youtube_id VARCHAR(100),
    track_1001_id VARCHAR(100),
    
    -- DJ metadata
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    color VARCHAR(20),
    comment TEXT,
    play_count INTEGER DEFAULT 0,
    
    -- File location
    file_path TEXT,
    
    -- Dates
    release_date DATE,
    added_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_played TIMESTAMP WITH TIME ZONE,
    
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tracks_title ON music.tracks USING gin(title gin_trgm_ops);
CREATE INDEX idx_tracks_artist ON music.tracks(artist_id);
CREATE INDEX idx_tracks_album ON music.tracks(album_id);
CREATE INDEX idx_tracks_isrc ON music.tracks(isrc);
CREATE INDEX idx_tracks_bpm ON music.tracks(bpm);
CREATE INDEX idx_tracks_key ON music.tracks(key);

-- Genres table
CREATE TABLE IF NOT EXISTS music.genres (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    parent_genre_id UUID REFERENCES music.genres(id),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Track-Genre junction table
CREATE TABLE IF NOT EXISTS music.track_genres (
    track_id UUID REFERENCES music.tracks(id) ON DELETE CASCADE,
    genre_id UUID REFERENCES music.genres(id) ON DELETE CASCADE,
    PRIMARY KEY (track_id, genre_id)
);

-- ====================================
-- Rekordbox Tables
-- ====================================

-- Rekordbox tracks (mirror of decrypted data)
CREATE TABLE IF NOT EXISTS rekordbox.tracks (
    id VARCHAR(100) PRIMARY KEY,
    music_track_id UUID REFERENCES music.tracks(id),
    title VARCHAR(500),
    artist VARCHAR(255),
    album VARCHAR(500),
    genre VARCHAR(100),
    bpm DECIMAL(5,2),
    key VARCHAR(10),
    rating INTEGER,
    color INTEGER,
    comment TEXT,
    analyzed BOOLEAN DEFAULT FALSE,
    file_path TEXT,
    date_added TIMESTAMP,
    last_modified TIMESTAMP,
    play_count INTEGER DEFAULT 0,
    last_played TIMESTAMP,
    raw_data JSONB
);

-- Rekordbox cue points
CREATE TABLE IF NOT EXISTS rekordbox.cue_points (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    track_id VARCHAR(100) REFERENCES rekordbox.tracks(id) ON DELETE CASCADE,
    position_ms INTEGER NOT NULL,
    type VARCHAR(20),
    index INTEGER,
    name VARCHAR(100),
    color VARCHAR(20),
    comment TEXT
);

-- Rekordbox beat grids
CREATE TABLE IF NOT EXISTS rekordbox.beat_grids (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    track_id VARCHAR(100) REFERENCES rekordbox.tracks(id) ON DELETE CASCADE,
    first_beat_ms INTEGER,
    bpm DECIMAL(5,2),
    manually_adjusted BOOLEAN DEFAULT FALSE
);

-- Rekordbox playlists
CREATE TABLE IF NOT EXISTS rekordbox.playlists (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    parent_id VARCHAR(100) REFERENCES rekordbox.playlists(id),
    is_folder BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Rekordbox playlist tracks
CREATE TABLE IF NOT EXISTS rekordbox.playlist_tracks (
    playlist_id VARCHAR(100) REFERENCES rekordbox.playlists(id) ON DELETE CASCADE,
    track_id VARCHAR(100) REFERENCES rekordbox.tracks(id) ON DELETE CASCADE,
    position INTEGER,
    PRIMARY KEY (playlist_id, track_id, position)
);

-- ====================================
-- Download & Source Tables
-- ====================================

-- Download sources
CREATE TABLE IF NOT EXISTS music.download_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    track_id UUID REFERENCES music.tracks(id),
    source_type VARCHAR(50) NOT NULL,
    source_user VARCHAR(255),
    quality VARCHAR(20),
    file_size BIGINT,
    download_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'
);

-- P2P sources
CREATE TABLE IF NOT EXISTS music.p2p_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) NOT NULL,
    network VARCHAR(50) NOT NULL,
    reputation DECIMAL(3,2),
    shared_files INTEGER,
    connection_quality VARCHAR(50),
    last_seen TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);

-- ====================================
-- Functions & Triggers
-- ====================================

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers to all tables with updated_at
CREATE TRIGGER update_artists_updated_at BEFORE UPDATE ON music.artists
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_albums_updated_at BEFORE UPDATE ON music.albums
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tracks_updated_at BEFORE UPDATE ON music.tracks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ====================================
-- Initial Data
-- ====================================

-- Insert common genres
INSERT INTO music.genres (name) VALUES 
    ('Electronic'),
    ('House'),
    ('Techno'),
    ('Trance'),
    ('Drum & Bass'),
    ('Dubstep'),
    ('Hip Hop'),
    ('Rock'),
    ('Pop'),
    ('Jazz')
ON CONFLICT (name) DO NOTHING;

-- Create materialized view for track search
CREATE MATERIALIZED VIEW IF NOT EXISTS music.track_search AS
SELECT 
    t.id,
    t.title,
    a.name as artist_name,
    al.title as album_title,
    t.bpm,
    t.key,
    t.energy,
    t.danceability,
    to_tsvector('english', 
        COALESCE(t.title, '') || ' ' || 
        COALESCE(a.name, '') || ' ' || 
        COALESCE(al.title, '')
    ) as search_vector
FROM music.tracks t
LEFT JOIN music.artists a ON t.artist_id = a.id
LEFT JOIN music.albums al ON t.album_id = al.id;

CREATE INDEX idx_track_search_vector ON music.track_search USING gin(search_vector);

-- Refresh function for materialized view
CREATE OR REPLACE FUNCTION refresh_track_search()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY music.track_search;
END;
$$ LANGUAGE plpgsql;