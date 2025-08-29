"""Rich CLI interface for the music agent."""

import time
from typing import Any, Dict, List

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown

from ..agent.core import MusicAgent
from ..utils.config import config
from ..auth.deezer_auth import DeezerAuthHelper
from ..auth.spotify_auth import SpotifyAuthHelper
from ..auth.youtube_auth import YouTubeAuthHelper


class MusicAgentCLI:
    """Rich CLI interface for the music agent."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.console = Console()
        self.agent = None
        self.deezer_auth = DeezerAuthHelper(self.console)
        self.spotify_auth = SpotifyAuthHelper(self.console)
        self.youtube_auth = YouTubeAuthHelper(self.console)
        
    def initialize_agent(self):
        """Initialize the music agent with progress display."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Initializing music agent...", total=None)
            
            try:
                self.agent = MusicAgent()
                progress.update(task, description="✅ Music agent initialized successfully!")
                time.sleep(1)  # Brief pause to show success
                return True
                
            except Exception as e:
                progress.update(task, description=f"❌ Failed to initialize agent: {str(e)}")
                time.sleep(2)  # Show error longer
                return False
    
    def show_banner(self):
        """Display the application banner."""
        banner_text = """
# 🎵 Music Discovery Agent

*AI-powered multi-platform music discovery and management*

**Powered by:** AWS Strands • OpenAI
**Platforms:** Deezer • Spotify • YouTube
        """
        
        banner = Panel(
            Markdown(banner_text),
            title="Welcome",
            title_align="center",
            border_style="cyan",
            padding=(1, 2)
        )
        
        self.console.print(banner)
        self.console.print()
    
    def show_agent_status(self):
        """Display agent status information."""
        if not self.agent:
            self.console.print("❌ Agent not initialized", style="red")
            return
            
        status = self.agent.get_agent_status()
        
        # Create status table
        table = Table(title="🤖 Agent Status", show_header=True, header_style="cyan")
        table.add_column("Provider", style="white", width=12)
        table.add_column("Model", style="blue", width=25)
        table.add_column("Status", style="green", width=12)
        table.add_column("API Key", style="yellow", width=12)
        
        # Agent row
        agent_info = status['agent']
        config_info = status['configuration']
        agent_status = "✅ Available" if agent_info['available'] else "❌ Not available"
        
        table.add_row(
            agent_info['provider'],
            agent_info['model'], 
            agent_status,
            config_info['api_key']
        )
        
        self.console.print(table)
        self.console.print()
    
    def show_configuration(self):
        """Display configuration information."""
        config_info = [
            f"**Agent Name:** {config.agent.name}",
            f"**Database:** {config.database.url}",
            f"**Model Provider:** OpenAI",
            f"**OpenAI Model:** {config.openai.model}",
            f"**Cache Directory:** {config.agent.cache_dir}",
            f"**Bedrock Model (future):** {config.aws.bedrock_model_id}",
        ]
        
        # Service status
        services = []
        if config.deezer.arl:
            services.append("✅ Deezer")
        else:
            services.append("❌ Deezer")
            
        if config.spotify.username:
            services.append("✅ Spotify") 
        else:
            services.append("❌ Spotify")
            
        if config.youtube.cookies_file:
            services.append("✅ YouTube")
        else:
            services.append("⚠️ YouTube (basic)")
            
        config_info.append(f"**Music Services:** {' • '.join(services)}")
        
        config_panel = Panel(
            "\n".join(config_info),
            title="⚙️ Configuration",
            border_style="green",
            padding=(1, 2)
        )
        
        self.console.print(config_panel)
        self.console.print()
    
    def display_search_results(self, results: List[Dict[str, Any]], query: str):
        """Display search results in a formatted table."""
        if not results:
            self.console.print(f"❌ No results found for: [bold]{query}[/bold]", style="red")
            return
            
        table = Table(title=f"🔍 Search Results for '{query}'", show_header=True)
        table.add_column("#", style="dim", width=3)
        table.add_column("Artist", style="cyan", width=20)
        table.add_column("Title", style="white", width=25)
        table.add_column("Platform", style="yellow", width=10)
        table.add_column("Duration", style="green", width=8)
        table.add_column("Available", style="blue", width=10)
        
        for i, result in enumerate(results[:20], 1):  # Limit to 20 results
            duration = f"{result.get('duration', 0)}s" if result.get('duration') else "N/A"
            available = "✅ Yes" if result.get('available', True) else "❌ No"
            
            table.add_row(
                str(i),
                result.get('artist', 'Unknown')[:18],
                result.get('title', 'Unknown')[:23],
                result.get('platform', 'Unknown'),
                duration,
                available
            )
        
        self.console.print(table)
        self.console.print()
    
    def show_help(self):
        """Display help information."""
        help_content = """
## Available Commands

**🔍 Search & Discovery**
- `search <query>` - Search for music across all platforms
- `search deezer <query>` - Search only on Deezer  
- `search spotify <query>` - Search only on Spotify
- `search youtube <query>` - Search only on YouTube

**📝 Playlist Management**
- `create playlist <name>` - Create a new playlist
- `list playlists` - Show all playlists
- `playlist <name>` - View playlist details

**📊 Analytics**  
- `trends` - Show listening trends (last month)
- `trends week` - Show weekly trends
- `trends year` - Show yearly trends

**🔐 Authentication**
- `auth deezer` - Setup Deezer authentication (ARL cookie)
- `auth spotify` - Setup Spotify authentication (username/password)
- `auth youtube` - Setup YouTube authentication (cookies file)
- `auth test` - Test current authentication status
- `auth status` - Show authentication status for all services

**🤖 Agent Management**
- `status` - Show agent and provider status
- `config` - Show configuration details

**ℹ️ Utility**
- `help` - Show this help
- `clear` - Clear the screen
- `quit` or `exit` - Exit the application

## Natural Language Queries

You can also use natural language:
- "Find me some jazz music from the 1960s"
- "Create a road trip playlist with rock music"
- "What are the top songs by The Beatles?"
- "Show me my listening history for last week"
        """
        
        help_panel = Panel(
            Markdown(help_content),
            title="📖 Help",
            border_style="blue",
            padding=(1, 2)
        )
        
        self.console.print(help_panel)
        self.console.print()
    
    def process_search_command(self, command: str):
        """Process search commands."""
        parts = command.strip().split(maxsplit=2)
        
        if len(parts) < 2:
            self.console.print("❌ Usage: search <query> or search <platform> <query>", style="red")
            return
            
        # Determine platform and query
        if len(parts) == 2:
            # search <query>
            platform = "all"
            query = parts[1]
        else:
            # search <platform> <query>
            potential_platform = parts[1].lower()
            if potential_platform in ["deezer", "spotify", "youtube", "all"]:
                platform = potential_platform
                query = parts[2]
            else:
                # Treat as "search <full query>"
                platform = "all"
                query = " ".join(parts[1:])
        
        # Show search progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task(f"Searching {platform} for '{query}'...", total=None)
            
            try:
                results = self.agent.search(query, platform, limit=20)
                progress.update(task, description=f"✅ Found {len(results)} results")
                time.sleep(0.5)
                
            except Exception as e:
                progress.update(task, description=f"❌ Search failed: {str(e)}")
                time.sleep(2)
                return
        
        self.display_search_results(results, query)
    
    def process_auth_command(self, command: str):
        """Process authentication commands."""
        parts = command.strip().split(maxsplit=1)
        
        if len(parts) == 1:
            self.console.print("❌ Usage: auth <deezer|spotify|youtube|test|status>", style="red")
            return
            
        auth_type = parts[1].lower()
        
        if auth_type == "deezer":
            self.handle_deezer_auth()
        elif auth_type == "spotify":
            self.handle_spotify_auth()
        elif auth_type == "youtube":
            self.handle_youtube_auth()
        elif auth_type == "test":
            self.test_all_auth()
        elif auth_type == "status":
            self.show_auth_status()
        else:
            self.console.print(f"❌ Unknown auth command: {auth_type}", style="red")
            self.console.print("💡 Available: auth deezer, auth spotify, auth youtube, auth test, auth status")
    
    def handle_deezer_auth(self):
        """Handle Deezer authentication setup."""
        try:
            arl = self.deezer_auth.start_auth_flow()
            if arl:
                # Suggest saving to .env file
                self.console.print()
                self.console.print("💾 To save this ARL permanently, add it to your .env file:", style="yellow")
                self.console.print(f"   DEEZER_ARL={arl}")
                self.console.print()
                
        except Exception as e:
            self.console.print(f"❌ Authentication error: {e}", style="red")
    
    def handle_spotify_auth(self):
        """Handle Spotify authentication setup."""
        try:
            credentials = self.spotify_auth.start_auth_flow()
            if credentials:
                # Suggest saving to .env file
                self.console.print()
                self.console.print("💾 To save these credentials permanently, add them to your .env file:", style="yellow")
                self.console.print(f"   SPOTIFY_USERNAME={credentials['username']}")
                self.console.print(f"   SPOTIFY_PASSWORD={credentials['password']}")
                if credentials.get("totp_secret"):
                    self.console.print(f"   SPOTIFY_TOTP_SECRET={credentials['totp_secret']}")
                self.console.print()
                
        except Exception as e:
            self.console.print(f"❌ Authentication error: {e}", style="red")
    
    def handle_youtube_auth(self):
        """Handle YouTube authentication setup."""
        try:
            cookies_file = self.youtube_auth.start_auth_flow()
            if cookies_file:
                # Suggest saving to .env file
                self.console.print()
                self.console.print("💾 To save this cookies file permanently, add it to your .env file:", style="yellow")
                self.console.print(f"   YOUTUBE_COOKIES_FILE={cookies_file}")
                self.console.print()
                
        except Exception as e:
            self.console.print(f"❌ Authentication error: {e}", style="red")
    
    def test_all_auth(self):
        """Test authentication for all services."""
        self.console.print("🔍 Testing authentication for all services...")
        self.console.print()
        
        # Test all services
        deezer_result = self.deezer_auth.quick_test()
        spotify_result = self.spotify_auth.quick_test()
        youtube_result = self.youtube_auth.quick_test()
        
        # Summary
        working_services = sum([deezer_result, spotify_result, youtube_result])
        
        if working_services > 0:
            self.console.print(f"\n✅ {working_services}/3 services are authenticated!", style="green")
        else:
            self.console.print("\n⚠️  No services are currently authenticated", style="yellow")
        
        if working_services < 3:
            self.console.print("💡 Use 'auth <service>' to set up missing services", style="cyan")
    
    def show_auth_status(self):
        """Show authentication status for all services."""
        status_table = Table(title="🔐 Authentication Status", show_header=True)
        status_table.add_column("Service", style="cyan", width=12)
        status_table.add_column("Status", style="white", width=15)
        status_table.add_column("Details", style="yellow", width=30)
        
        # Deezer status
        if config.deezer.arl:
            try:
                from ..integrations.deezer import DeezerIntegration
                deezer = DeezerIntegration()
                if deezer.user_id:
                    status_table.add_row("Deezer", "✅ Authenticated", f"User ID: {deezer.user_id}")
                else:
                    status_table.add_row("Deezer", "❌ Invalid", "ARL may be expired")
            except Exception:
                status_table.add_row("Deezer", "❌ Error", "Failed to test ARL")
        else:
            status_table.add_row("Deezer", "❌ Not configured", "No ARL cookie found")
        
        # Spotify status
        if config.spotify.username and config.spotify.password:
            try:
                from ..integrations.spotify import SpotifyIntegration
                spotify = SpotifyIntegration()
                if spotify.access_token:
                    status_table.add_row("Spotify", "✅ Authenticated", f"Logged in as {config.spotify.username}")
                else:
                    status_table.add_row("Spotify", "❌ Invalid", "Credentials may be wrong")
            except Exception:
                status_table.add_row("Spotify", "❌ Error", "Failed to test credentials")
        else:
            status_table.add_row("Spotify", "❌ Not configured", "No credentials found")
        
        # YouTube status  
        if config.youtube.cookies_file:
            try:
                from ..integrations.youtube import YouTubeIntegration
                youtube = YouTubeIntegration(cookies_file=config.youtube.cookies_file)
                test_results = youtube.search("test", limit=1)
                if test_results:
                    status_table.add_row("YouTube", "✅ Authenticated", "Cookies working")
                else:
                    status_table.add_row("YouTube", "⚠️  Limited", "Cookies may be expired")
            except Exception:
                status_table.add_row("YouTube", "❌ Error", "Failed to test cookies")
        else:
            status_table.add_row("YouTube", "⚠️  Basic mode", "No cookies file")
            
        self.console.print(status_table)
        self.console.print()
    
    def process_agent_query(self, query: str):
        """Process natural language query through the agent."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Processing your request...", total=None)
            
            try:
                response = self.agent.chat(query)
                progress.update(task, description="✅ Request processed")
                time.sleep(0.5)
                
            except Exception as e:
                progress.update(task, description=f"❌ Request failed: {str(e)}")
                time.sleep(2)
                return
        
        # Display response in a panel
        response_panel = Panel(
            response,
            title="🤖 Agent Response",
            border_style="magenta",
            padding=(1, 2)
        )
        
        self.console.print(response_panel)
        self.console.print()
    
    def run_interactive_mode(self):
        """Run the interactive CLI mode."""
        self.show_banner()
        
        # Initialize agent
        if not self.initialize_agent():
            self.console.print("❌ Failed to initialize agent. Exiting.", style="red")
            return
            
        self.show_agent_status()
        
        self.console.print("💡 Type [bold cyan]help[/bold cyan] for commands, or ask me anything in natural language!")
        self.console.print("💡 Type [bold red]quit[/bold red] or [bold red]exit[/bold red] to stop\n")
        
        while True:
            try:
                # Get user input with rich prompt
                user_input = Prompt.ask(
                    "[bold cyan]🎵[/bold cyan]",
                    console=self.console
                ).strip()
                
                if not user_input:
                    continue
                    
                # Handle exit commands
                if user_input.lower() in ["quit", "exit", "q"]:
                    if Confirm.ask("Are you sure you want to exit?", console=self.console):
                        break
                    continue
                
                # Handle built-in commands
                if user_input.lower() == "help":
                    self.show_help()
                    continue
                    
                elif user_input.lower() == "status":
                    self.show_agent_status()
                    continue
                    
                elif user_input.lower() == "config":
                    self.show_configuration()
                    continue
                    
                elif user_input.lower() == "clear":
                    self.console.clear()
                    self.show_banner()
                    continue
                    
                elif user_input.lower().startswith("search"):
                    self.process_search_command(user_input)
                    continue
                    
                elif user_input.lower().startswith("auth"):
                    self.process_auth_command(user_input)
                    continue
                
                # Handle as natural language query
                self.process_agent_query(user_input)
                
            except KeyboardInterrupt:
                if Confirm.ask("\n🛑 Exit the music agent?", console=self.console):
                    break
                continue
                
            except EOFError:
                break
                
            except Exception as e:
                self.console.print(f"❌ Unexpected error: {str(e)}", style="red")
                continue
        
        self.console.print("\n👋 Thanks for using Music Discovery Agent!", style="cyan")


def run_cli():
    """Main CLI entry point."""
    cli = MusicAgentCLI()
    cli.run_interactive_mode()