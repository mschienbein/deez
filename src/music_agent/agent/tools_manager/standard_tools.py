"""
Standard tools provider for the music agent.
"""

import logging
from typing import List, Any
from strands_tools import (
    calculator,
    current_time,
    file_read,
    file_write,
    http_request,
    python_repl,
    shell,
    use_aws,
)

logger = logging.getLogger(__name__)


class StandardToolsProvider:
    """Provides standard Strands tools for the agent."""
    
    @staticmethod
    def get_standard_tools() -> List[Any]:
        """
        Get all standard Strands tools.
        
        Returns:
            List of standard tool functions
        """
        return [
            http_request,
            python_repl,
            shell,
            file_read,
            file_write,
            calculator,
            current_time,
            use_aws,
        ]
    
    @staticmethod
    def get_basic_tools() -> List[Any]:
        """
        Get basic tools (no shell/file operations).
        
        Returns:
            List of basic tool functions
        """
        return [
            http_request,
            calculator,
            current_time,
        ]
    
    @staticmethod
    def get_file_tools() -> List[Any]:
        """
        Get file operation tools.
        
        Returns:
            List of file operation tools
        """
        return [
            file_read,
            file_write,
        ]
    
    @staticmethod
    def get_system_tools() -> List[Any]:
        """
        Get system operation tools.
        
        Returns:
            List of system tools
        """
        return [
            shell,
            python_repl,
            use_aws,
        ]