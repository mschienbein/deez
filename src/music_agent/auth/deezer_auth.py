"""Deezer authentication helper with guided ARL cookie extraction."""

import webbrowser
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown

from ..integrations.deezer import DeezerIntegration


class DeezerAuthHelper:
    """Helper for Deezer authentication through guided ARL extraction."""
    
    def __init__(self, console: Optional[Console] = None):
        """Initialize the authentication helper."""
        self.console = console or Console()
    
    def start_auth_flow(self) -> Optional[str]:
        """Start the guided authentication flow to get ARL cookie."""
        self.console.print()
        
        # Show introduction
        intro_text = """
# 🎵 Deezer Authentication Setup

Since Deezer doesn't have a public OAuth API, we need to extract your **ARL cookie** 
from your browser after logging into Deezer.

**What is ARL?** 
ARL (Authorization Request Login) is a session token that Deezer uses to authenticate users.

**Why is this needed?**
- Access your personal playlists and favorites
- Search with higher quality results
- Download tracks (with premium subscription)

⚠️  **Important:** Never share your ARL cookie with others - it's like your password!
        """
        
        intro_panel = Panel(
            Markdown(intro_text),
            title="Authentication Required",
            border_style="yellow",
            padding=(1, 2)
        )
        
        self.console.print(intro_panel)
        self.console.print()
        
        # Ask if user wants to continue
        if not Confirm.ask("Would you like to set up Deezer authentication?"):
            return None
        
        # Guide user through browser steps
        self._show_browser_instructions()
        
        # Open Deezer in browser
        if Confirm.ask("Would you like me to open Deezer in your browser?"):
            webbrowser.open("https://www.deezer.com/login")
            self.console.print("✅ Opened Deezer in your browser")
        else:
            self.console.print("📝 Please manually navigate to: https://www.deezer.com/login")
        
        self.console.print()
        
        # Wait for user to complete login
        Prompt.ask("Press Enter after you've logged into Deezer", default="")
        
        # Show cookie extraction instructions
        arl_cookie = self._guide_cookie_extraction()
        
        if arl_cookie:
            # Test the cookie
            if self._test_arl_cookie(arl_cookie):
                self._show_success_instructions(arl_cookie)
                return arl_cookie
            else:
                self.console.print("❌ The ARL cookie appears to be invalid. Please try again.", style="red")
                return None
        
        return None
    
    def _show_browser_instructions(self):
        """Show instructions for browser login."""
        instructions = """
## 📋 Step-by-Step Instructions:

1. **Login to Deezer** - Use your username/password or social login
2. **Open Developer Tools** - Press F12 (or right-click → Inspect)
3. **Go to Application/Storage tab** - Look for cookies section
4. **Find the ARL cookie** - Look for a cookie named "arl"
5. **Copy the ARL value** - Copy the long string value (not the name)

**The ARL cookie looks like:**
`136b0d2c4b12a86sdkj2c3f21c4b12a86sdkj2c3f21c4b12a86sdkj2c3f21c4b12a86s`
        """
        
        instructions_panel = Panel(
            Markdown(instructions),
            title="🔧 How to Extract ARL Cookie",
            border_style="blue",
            padding=(1, 2)
        )
        
        self.console.print(instructions_panel)
        self.console.print()
    
    def _guide_cookie_extraction(self) -> Optional[str]:
        """Guide user through cookie extraction."""
        self.console.print("🔍 Now let's extract your ARL cookie from the browser:")
        self.console.print()
        
        # Detailed step-by-step guidance
        steps = [
            "1. In your browser with Deezer open, press **F12** to open Developer Tools",
            "2. Click on the **Application** tab (Chrome) or **Storage** tab (Firefox)",
            "3. In the left sidebar, expand **Cookies** and click on **https://www.deezer.com**",
            "4. Look for a cookie named **'arl'** in the list",
            "5. Click on the 'arl' cookie row",
            "6. Copy the **Value** (the long string, not the name)",
        ]
        
        for step in steps:
            self.console.print(f"   {step}")
        
        self.console.print()
        self.console.print("💡 The ARL value is typically 130+ characters long and contains letters and numbers")
        self.console.print()
        
        # Get ARL from user
        while True:
            arl_input = Prompt.ask("Paste your ARL cookie value here", password=True)
            
            if not arl_input:
                if not Confirm.ask("No ARL provided. Would you like to try again?"):
                    return None
                continue
            
            # Basic validation
            if len(arl_input) < 100:
                self.console.print("⚠️  The ARL seems too short. Please make sure you copied the full value.", style="yellow")
                if not Confirm.ask("Continue with this ARL anyway?"):
                    continue
            
            # Clean up the ARL (remove quotes, whitespace)
            arl_cleaned = arl_input.strip().strip('"').strip("'")
            
            return arl_cleaned
    
    def _test_arl_cookie(self, arl: str) -> bool:
        """Test if the ARL cookie is valid."""
        self.console.print("🧪 Testing your ARL cookie...")
        
        try:
            # Create a test Deezer integration
            deezer = DeezerIntegration(arl=arl)
            
            # Try to get user data
            if deezer.user_id:
                self.console.print(f"✅ ARL is valid! Authenticated as user ID: {deezer.user_id}", style="green")
                return True
            else:
                self.console.print("❌ ARL authentication failed", style="red")
                return False
                
        except Exception as e:
            self.console.print(f"❌ Error testing ARL: {e}", style="red")
            return False
    
    def _show_success_instructions(self, arl: str):
        """Show success message and next steps."""
        success_text = f"""
# ✅ Authentication Successful!

Your Deezer ARL has been validated and is working correctly.

## 🔐 Secure Your ARL

**Add to your `.env` file:**
```bash
DEEZER_ARL={arl}
```

## ⚠️ Security Notes:

- **Keep this ARL private** - Don't share it with anyone
- **It expires periodically** - You may need to refresh it later
- **One device at a time** - Using the same ARL on multiple devices may cause issues

## 🎵 What You Can Now Do:

- ✅ Access your personal playlists and favorites
- ✅ Search with enhanced results
- ✅ Download tracks (with Deezer Premium)
- ✅ Use all advanced Deezer features in the music agent

The music agent will now automatically use your Deezer authentication!
        """
        
        success_panel = Panel(
            Markdown(success_text),
            title="🎉 Setup Complete",
            border_style="green",
            padding=(1, 2)
        )
        
        self.console.print(success_panel)
    
    def quick_test(self, arl: Optional[str] = None) -> bool:
        """Quick test of existing ARL configuration."""
        if not arl:
            from ..utils.config import config
            arl = config.deezer.arl
            
        if not arl:
            self.console.print("❌ No Deezer ARL configured", style="red")
            return False
        
        self.console.print("🔍 Testing Deezer authentication...")
        
        try:
            deezer = DeezerIntegration(arl=arl)
            if deezer.user_id:
                self.console.print(f"✅ Deezer authentication working (User ID: {deezer.user_id})", style="green")
                return True
            else:
                self.console.print("❌ Deezer authentication failed - ARL may be expired", style="red")
                return False
                
        except Exception as e:
            self.console.print(f"❌ Deezer test error: {e}", style="red")
            return False


def run_deezer_auth():
    """Standalone function to run Deezer authentication."""
    helper = DeezerAuthHelper()
    return helper.start_auth_flow()