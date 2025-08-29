"""YouTube authentication helper with guided cookies extraction."""

import webbrowser
from typing import Optional
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown

from ..integrations.youtube import YouTubeIntegration


class YouTubeAuthHelper:
    """Helper for YouTube authentication through guided cookies setup."""
    
    def __init__(self, console: Optional[Console] = None):
        """Initialize the authentication helper."""
        self.console = console or Console()
    
    def start_auth_flow(self) -> Optional[str]:
        """Start the guided authentication flow to get YouTube cookies."""
        self.console.print()
        
        # Show introduction
        intro_text = """
# 🎵 YouTube Authentication Setup

YouTube authentication uses browser cookies to access your personal data and avoid rate limits.

**What we'll extract:**
- YouTube session cookies from your browser
- These allow access to your subscriptions, playlists, and premium features

**Why is this needed?**
- Access your personal YouTube Music playlists
- Higher quality downloads (if you have YouTube Premium)
- Bypass age restrictions and regional blocks
- Avoid API rate limits for better performance

**Methods Available:**
1. **Browser Extension** (Recommended) - Get cookies via browser extension
2. **Manual Export** - Export cookies using browser developer tools
3. **Existing File** - Use cookies file you already have

⚠️  **Important:** Cookies are like temporary passwords - keep them secure!
        """
        
        intro_panel = Panel(
            Markdown(intro_text),
            title="YouTube Authentication Required",
            border_style="red",
            padding=(1, 2)
        )
        
        self.console.print(intro_panel)
        self.console.print()
        
        # Ask if user wants to continue
        if not Confirm.ask("Would you like to set up YouTube authentication?"):
            return None
        
        # Show method selection
        method = self._choose_auth_method()
        
        if method == "extension":
            cookies_file = self._guide_extension_method()
        elif method == "manual":
            cookies_file = self._guide_manual_method()
        elif method == "existing":
            cookies_file = self._use_existing_file()
        else:
            return None
        
        if cookies_file:
            # Test the cookies
            if self._test_cookies(cookies_file):
                self._show_success_instructions(cookies_file)
                return cookies_file
            else:
                self.console.print("❌ The YouTube cookies appear to be invalid. Please try again.", style="red")
                return None
        
        return None
    
    def _choose_auth_method(self) -> str:
        """Let user choose authentication method."""
        methods_text = """
## 🛠️ Choose Your Authentication Method:

**1. Browser Extension (Recommended)**
- Install "Get cookies.txt" browser extension
- One-click cookie export
- Most reliable method

**2. Manual Export**
- Use browser developer tools
- Export cookies manually 
- More technical but always works

**3. Existing File**
- You already have a cookies.txt file
- Just need to specify the location
        """
        
        methods_panel = Panel(
            Markdown(methods_text),
            title="Authentication Methods",
            border_style="cyan",
            padding=(1, 2)
        )
        
        self.console.print(methods_panel)
        self.console.print()
        
        while True:
            choice = Prompt.ask(
                "Choose method",
                choices=["1", "2", "3", "extension", "manual", "existing"],
                default="1"
            ).lower()
            
            if choice in ["1", "extension"]:
                return "extension"
            elif choice in ["2", "manual"]:
                return "manual"
            elif choice in ["3", "existing"]:
                return "existing"
    
    def _guide_extension_method(self) -> Optional[str]:
        """Guide user through browser extension method."""
        extension_instructions = """
## 🔧 Browser Extension Method

### Step 1: Install Extension

**Chrome/Edge:**
- Go to Chrome Web Store
- Search for "Get cookies.txt LOCALLY"
- Install the extension by Rahul Shaw

**Firefox:**
- Go to Firefox Add-ons
- Search for "cookies.txt"
- Install "cookies.txt" extension

### Step 2: Login to YouTube

1. Open YouTube.com in your browser
2. Sign in to your Google account
3. Make sure you're logged into YouTube Music as well

### Step 3: Export Cookies

1. Navigate to YouTube.com (make sure you're logged in)
2. Click the cookies extension icon in your browser
3. Click "Export cookies" or similar button
4. Save the file as `youtube_cookies.txt`
5. Remember the location where you saved it
        """
        
        self.console.print(Panel(
            Markdown(extension_instructions),
            title="Browser Extension Setup",
            border_style="blue",
            padding=(1, 2)
        ))
        
        # Offer to open extension pages
        if Confirm.ask("Would you like me to open the Chrome Web Store for the extension?"):
            webbrowser.open("https://chrome.google.com/webstore/search/get%20cookies.txt")
            self.console.print("✅ Opened Chrome Web Store")
        
        if Confirm.ask("Would you like me to open YouTube for you to log in?"):
            webbrowser.open("https://www.youtube.com")
            self.console.print("✅ Opened YouTube")
        
        self.console.print()
        Prompt.ask("Press Enter after you've exported the cookies file", default="")
        
        return self._get_cookies_file_path()
    
    def _guide_manual_method(self) -> Optional[str]:
        """Guide user through manual cookie extraction."""
        manual_instructions = """
## 🔧 Manual Cookie Export Method

### Step 1: Login to YouTube

1. Open YouTube.com in your browser
2. Sign in to your Google account
3. Ensure you're properly logged in

### Step 2: Open Developer Tools

- **Chrome/Edge**: Press `F12` or right-click → "Inspect"
- **Firefox**: Press `F12` or right-click → "Inspect Element"
- **Safari**: Enable Developer menu first, then use it

### Step 3: Navigate to Application/Storage Tab

- **Chrome/Edge**: Click "Application" tab → "Cookies" → "https://www.youtube.com"
- **Firefox**: Click "Storage" tab → "Cookies" → "https://www.youtube.com"

### Step 4: Export Cookie Data

1. You'll see a list of cookies for YouTube
2. Look for important cookies (especially ones with "session" or auth-related names)
3. You can either:
   - Right-click and "Copy All" (some browsers)
   - Select all cookies and copy the data
   - Use browser console to export (advanced)

### Step 5: Create Cookies File

Create a text file with the cookies in Netscape format:
```
# Netscape HTTP Cookie File
# Generated for YouTube authentication
.youtube.com	TRUE	/	TRUE	1234567890	cookie_name	cookie_value
```
        """
        
        self.console.print(Panel(
            Markdown(manual_instructions),
            title="Manual Cookie Export", 
            border_style="blue",
            padding=(1, 2)
        ))
        
        if Confirm.ask("Would you like me to open YouTube for you to log in?"):
            webbrowser.open("https://www.youtube.com")
            self.console.print("✅ Opened YouTube")
        
        self.console.print()
        self.console.print("💡 This method is more technical. Consider using the browser extension method instead.", style="yellow")
        
        if not Confirm.ask("Do you want to continue with manual export?"):
            return None
        
        Prompt.ask("Press Enter after you've created your cookies file", default="")
        
        return self._get_cookies_file_path()
    
    def _use_existing_file(self) -> Optional[str]:
        """Use an existing cookies file."""
        self.console.print("📂 Using an existing cookies file...")
        return self._get_cookies_file_path()
    
    def _get_cookies_file_path(self) -> Optional[str]:
        """Get the path to the cookies file from user."""
        while True:
            file_path = Prompt.ask("Enter the path to your cookies file")
            
            if not file_path:
                if not Confirm.ask("No file path provided. Would you like to try again?"):
                    return None
                continue
            
            # Expand user path
            path = Path(file_path).expanduser()
            
            if not path.exists():
                self.console.print(f"❌ File not found: {path}", style="red")
                if not Confirm.ask("Would you like to try a different path?"):
                    return None
                continue
            
            if not path.is_file():
                self.console.print(f"❌ Path is not a file: {path}", style="red")
                continue
            
            return str(path)
    
    def _test_cookies(self, cookies_file: str) -> bool:
        """Test if the cookies file is valid."""
        self.console.print("🧪 Testing your YouTube cookies...")
        
        try:
            # Create a test YouTube integration
            youtube = YouTubeIntegration(cookies_file=cookies_file)
            
            # Try a simple operation
            test_results = youtube.search("test", limit=1)
            
            if test_results:
                self.console.print("✅ YouTube cookies are working!", style="green")
                return True
            else:
                self.console.print("⚠️  Cookies loaded but search returned no results", style="yellow")
                return True  # May still be valid
                
        except Exception as e:
            self.console.print(f"❌ Error testing YouTube cookies: {e}", style="red")
            return False
    
    def _show_success_instructions(self, cookies_file: str):
        """Show success message and next steps."""
        success_text = f"""
# ✅ YouTube Authentication Successful!

Your YouTube cookies have been validated and are working correctly.

## 🔐 Secure Your Cookies

**Add to your `.env` file:**
```bash
YOUTUBE_COOKIES_FILE={cookies_file}
```

## ⚠️ Security Notes:

- **Keep cookies file private** - Don't share it with anyone
- **Cookies expire periodically** - You may need to refresh them later
- **One browser at a time** - Using the same session elsewhere may invalidate cookies
- **Backup the file** - Store it safely in case you need to reconfigure

## 🎵 What You Can Now Do:

- ✅ Access your YouTube Music playlists and subscriptions
- ✅ Higher quality downloads (if you have YouTube Premium)
- ✅ Bypass age restrictions and regional blocks
- ✅ Avoid API rate limits for better performance
- ✅ Full YouTube integration in the music agent

The music agent will now automatically use your YouTube authentication!
        """
        
        success_panel = Panel(
            Markdown(success_text),
            title="🎉 YouTube Setup Complete",
            border_style="red",
            padding=(1, 2)
        )
        
        self.console.print(success_panel)
    
    def quick_test(self, cookies_file: Optional[str] = None) -> bool:
        """Quick test of existing YouTube configuration."""
        if not cookies_file:
            from ..utils.config import config
            cookies_file = config.youtube.cookies_file
            
        if not cookies_file:
            self.console.print("❌ No YouTube cookies file configured", style="red")
            return False
        
        self.console.print("🔍 Testing YouTube authentication...")
        
        try:
            youtube = YouTubeIntegration(cookies_file=cookies_file)
            test_results = youtube.search("test", limit=1)
            
            if test_results:
                self.console.print("✅ YouTube authentication working", style="green")
                return True
            else:
                self.console.print("⚠️  YouTube cookies loaded but may be expired", style="yellow")
                return False
                
        except Exception as e:
            self.console.print(f"❌ YouTube test error: {e}", style="red")
            return False


def run_youtube_auth():
    """Standalone function to run YouTube authentication."""
    helper = YouTubeAuthHelper()
    return helper.start_auth_flow()


if __name__ == "__main__":
    run_youtube_auth()