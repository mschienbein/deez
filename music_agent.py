#!/usr/bin/env python3
"""Main application for the music discovery agent."""

import argparse
import logging
import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from music_agent.agent.core import MusicAgent
from music_agent.utils.config import config
from music_agent.cli.interface import MusicAgentCLI


def setup_logging():
    """Setup logging configuration."""
    log_level = getattr(logging, config.agent.log_level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("music_agent.log")
        ]
    )


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description="Music Discovery Agent")
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    parser.add_argument(
        "--query", "-q",
        type=str,
        help="Single query to process"
    )
    parser.add_argument(
        "--search", "-s",
        type=str,
        help="Search for music"
    )
    parser.add_argument(
        "--platform", "-p",
        type=str,
        default="all",
        choices=["all", "deezer", "spotify", "youtube"],
        help="Platform to search"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=10,
        help="Limit number of results"
    )
    parser.add_argument(
        "--config-check", "-c",
        action="store_true",
        help="Check configuration and exit"
    )
    
    args = parser.parse_args()
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Check configuration
        if args.config_check:
            print("Configuration:")
            print(f"  Agent Name: {config.agent.name}")
            print(f"  Database URL: {config.database.url}")
            print(f"  Primary Provider: {config.agent.primary_provider}")
            print(f"  Fallback Provider: {config.agent.fallback_provider}")
            print(f"  OpenAI API Key: {'Set' if config.openai.api_key else 'Not set'}")
            print(f"  OpenAI Model: {config.openai.model}")
            print(f"  AWS Region: {config.aws.region}")
            print(f"  Bedrock Model: {config.aws.bedrock_model_id}")
            print(f"  Deezer ARL: {'Set' if config.deezer.arl else 'Not set'}")
            print(f"  Spotify Username: {'Set' if config.spotify.username else 'Not set'}")
            print(f"  Cache Directory: {config.agent.cache_dir}")
            return
        
        if args.search or args.query:
            # Initialize agent for non-interactive modes
            logger.info("Initializing music agent...")
            agent = MusicAgent()
            
            # Show agent status
            status = agent.get_agent_status()
            print(f"\nAgent Status:")
            print(f"  Provider: {status['agent']['provider']} ({status['agent']['model']}) - {'Available' if status['agent']['available'] else 'Not available'}")
            print(f"  API Key: {status['configuration']['api_key']}")
            print()
        
        if args.search:
            # Direct search mode
            logger.info(f"Searching for: {args.search}")
            results = agent.search(args.search, args.platform, args.limit)
            
            if results:
                print(f"\nFound {len(results)} results:")
                for i, result in enumerate(results, 1):
                    print(f"{i}. {result.get('artist', 'Unknown')} - {result.get('title', 'Unknown')}")
                    print(f"   Platform: {result.get('platform', 'Unknown')}")
                    print(f"   Duration: {result.get('duration', 0)}s")
                    if result.get('platform_url'):
                        print(f"   URL: {result['platform_url']}")
                    print()
            else:
                print("No results found.")
                
        elif args.query:
            # Single query mode
            response = agent.chat(args.query)
            print(f"\nAgent: {response}")
            
        elif args.interactive:
            # Rich Interactive mode
            cli = MusicAgentCLI()
            cli.run_interactive_mode()
        
        else:
            # Default: show help
            parser.print_help()
        
        # Cleanup (only for non-interactive modes)
        if args.search or args.query:
            agent.close()
            logger.info("Music agent shutdown complete")
        
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()