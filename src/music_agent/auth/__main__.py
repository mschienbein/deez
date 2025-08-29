"""Main entry point for authentication module."""

import sys

def main():
    """Show available authentication commands."""
    print("🔐 Music Agent Authentication")
    print()
    print("Available authentication commands:")
    print("  uv run auth-deezer    - Setup Deezer authentication (ARL cookie)")
    print("  uv run auth-spotify   - Setup Spotify authentication (username/password)")
    print("  uv run auth-youtube   - Setup YouTube authentication (cookies file)")
    print()
    print("Or run individual modules:")
    print("  python -m music_agent.auth.deezer_auth")
    print("  python -m music_agent.auth.spotify_auth")
    print("  python -m music_agent.auth.youtube_auth")

if __name__ == "__main__":
    main()