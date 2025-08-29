"""Spotify authentication helper with guided credential and 2FA setup."""

import webbrowser
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown

from ..integrations.spotify import SpotifyIntegration


class SpotifyAuthHelper:
    """Helper for Spotify authentication through guided credential setup."""
    
    def __init__(self, console: Optional[Console] = None):
        """Initialize the authentication helper."""
        self.console = console or Console()
    
    def start_auth_flow(self) -> Optional[dict]:
        """Start the guided authentication flow to get Spotify credentials."""
        self.console.print()
        
        # Show introduction
        intro_text = """
# 🎵 Spotify Authentication Setup

To access your personal Spotify data and enhanced features, we need your login credentials.

**What we'll collect:**
- Username/email and password
- Two-Factor Authentication (2FA) secret (optional but recommended)

**Why is this needed?**
- Access your personal playlists and saved music
- Enhanced search results and recommendations  
- Full Spotify Web API access for advanced features

**Security Notes:**
- Credentials are stored locally in your .env file
- We use the same login method as the Spotify web player
- 2FA setup is optional but provides better security

⚠️  **Important:** Your credentials never leave your device!
        """
        
        intro_panel = Panel(
            Markdown(intro_text),
            title="Spotify Authentication Required", 
            border_style="green",
            padding=(1, 2)
        )
        
        self.console.print(intro_panel)
        self.console.print()
        
        # Ask if user wants to continue
        if not Confirm.ask("Would you like to set up Spotify authentication?"):
            return None
        
        # Guide user through credential setup
        credentials = self._get_credentials()
        
        if credentials:
            # Test the credentials
            if self._test_credentials(credentials):
                self._show_success_instructions(credentials)
                return credentials
            else:
                self.console.print("❌ The Spotify credentials appear to be invalid. Please try again.", style="red")
                return None
        
        return None
    
    def _get_credentials(self) -> Optional[dict]:
        """Get Spotify credentials from user."""
        self.console.print("📝 Let's set up your Spotify credentials:")
        self.console.print()
        
        # Get username/email
        username = Prompt.ask("Enter your Spotify username or email")
        if not username:
            self.console.print("❌ Username is required", style="red")
            return None
        
        # Get password
        password = Prompt.ask("Enter your Spotify password", password=True)
        if not password:
            self.console.print("❌ Password is required", style="red")
            return None
        
        credentials = {
            "username": username,
            "password": password
        }
        
        # Ask about 2FA
        self.console.print()
        if Confirm.ask("Do you have Two-Factor Authentication (2FA) enabled on your Spotify account?"):
            totp_secret = self._setup_2fa()
            if totp_secret:
                credentials["totp_secret"] = totp_secret
        
        return credentials
    
    def _setup_2fa(self) -> Optional[str]:
        """Guide user through 2FA setup."""
        self.console.print()
        
        twofa_instructions = """
## 🔐 Two-Factor Authentication Setup

To get your 2FA secret, you'll need to access your Spotify account settings.

### Step-by-Step Instructions:

1. **Open Spotify Account Settings**
   - Go to: https://www.spotify.com/account/
   - Sign in if prompted

2. **Navigate to Privacy Settings**
   - Scroll down to "Privacy Settings" section
   - Click on "Edit profile" or account settings

3. **Find Two-Factor Authentication**
   - Look for "Two-factor authentication" or "Security" section
   - You should see your authenticator app setup

4. **Get the Secret Key**
   - When you set up 2FA initially, Spotify showed a QR code
   - There's usually a "Can't scan?" or "Manual entry" link
   - Click that to reveal the secret key (long string of letters/numbers)

**The secret looks like:** `JBSWY3DPEHPK3PXP2VQ7M5HX4QZDTXKL`

**Don't have the secret?** You may need to disable and re-enable 2FA to get it.
        """
        
        instructions_panel = Panel(
            Markdown(twofa_instructions),
            title="🔧 How to Get Your 2FA Secret",
            border_style="blue", 
            padding=(1, 2)
        )
        
        self.console.print(instructions_panel)
        self.console.print()
        
        if Confirm.ask("Would you like me to open Spotify account settings in your browser?"):
            webbrowser.open("https://www.spotify.com/account/")
            self.console.print("✅ Opened Spotify account settings in your browser")
        
        self.console.print()
        
        # Get TOTP secret from user
        while True:
            totp_secret = Prompt.ask("Enter your 2FA secret key (or leave empty to skip)", default="")
            
            if not totp_secret:
                self.console.print("⚠️  Skipping 2FA setup. You may need to disable 2FA or enter codes manually.", style="yellow")
                return None
            
            # Basic validation
            # Remove spaces and convert to uppercase
            totp_secret = re.sub(r'[^A-Z0-9]', '', totp_secret.upper())
            
            if len(totp_secret) < 16:
                self.console.print("⚠️  The secret seems too short. Typical secrets are 16+ characters.", style="yellow")
                if not Confirm.ask("Continue with this secret anyway?"):
                    continue
            
            return totp_secret
    
    def _test_credentials(self, credentials: dict) -> bool:
        """Test if the credentials are valid."""
        self.console.print("🧪 Testing your Spotify credentials...")
        
        try:
            # Create a test Spotify integration
            spotify = SpotifyIntegration(
                username=credentials["username"],
                password=credentials["password"],
                totp_secret=credentials.get("totp_secret")
            )
            
            # Try to authenticate
            if spotify.access_token:
                self.console.print("✅ Spotify authentication successful!", style="green")
                return True
            else:
                self.console.print("❌ Spotify authentication failed", style="red")
                return False
                
        except Exception as e:
            self.console.print(f"❌ Error testing Spotify credentials: {e}", style="red")
            return False
    
    def _show_success_instructions(self, credentials: dict):
        """Show success message and next steps."""
        totp_line = f"SPOTIFY_TOTP_SECRET={credentials['totp_secret']}" if credentials.get("totp_secret") else "# SPOTIFY_TOTP_SECRET=your_2fa_secret  # Optional"
        
        success_text = f"""
# ✅ Spotify Authentication Successful!

Your Spotify credentials have been validated and are working correctly.

## 🔐 Secure Your Credentials

**Add to your `.env` file:**
```bash
SPOTIFY_USERNAME={credentials['username']}
SPOTIFY_PASSWORD={credentials['password']}
{totp_line}
```

## ⚠️ Security Notes:

- **Keep these credentials private** - Don't share them with anyone
- **They're stored locally only** - Never sent to external servers
- **2FA is recommended** - Provides extra security for your account
- **Change password periodically** - Good security practice

## 🎵 What You Can Now Do:

- ✅ Access your personal playlists and saved music
- ✅ Enhanced search results and recommendations
- ✅ Full Spotify Web API access
- ✅ Cross-platform playlist synchronization
- ✅ Advanced music discovery features

The music agent will now automatically use your Spotify authentication!
        """
        
        success_panel = Panel(
            Markdown(success_text),
            title="🎉 Spotify Setup Complete",
            border_style="green",
            padding=(1, 2)
        )
        
        self.console.print(success_panel)
    
    def quick_test(self, username: Optional[str] = None, password: Optional[str] = None, totp_secret: Optional[str] = None) -> bool:
        """Quick test of existing Spotify configuration."""
        if not (username and password):
            from ..utils.config import config
            username = username or config.spotify.username
            password = password or config.spotify.password  
            totp_secret = totp_secret or config.spotify.totp_secret
            
        if not (username and password):
            self.console.print("❌ No Spotify credentials configured", style="red")
            return False
        
        self.console.print("🔍 Testing Spotify authentication...")
        
        try:
            spotify = SpotifyIntegration(username=username, password=password, totp_secret=totp_secret)
            if spotify.access_token:
                self.console.print("✅ Spotify authentication working", style="green")
                return True
            else:
                self.console.print("❌ Spotify authentication failed - check credentials", style="red")
                return False
                
        except Exception as e:
            self.console.print(f"❌ Spotify test error: {e}", style="red")
            return False


def run_spotify_auth():
    """Standalone function to run Spotify authentication."""
    helper = SpotifyAuthHelper()
    return helper.start_auth_flow()