"""
User-related models for Soulseek.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

from .file import File


@dataclass
class UserInfo:
    """Information about a Soulseek user."""
    
    username: str
    description: Optional[str] = None
    picture: Optional[bytes] = None
    upload_slots: int = 0
    queue_length: int = 0
    has_free_slots: bool = False
    is_online: bool = False
    shared_file_count: Optional[int] = None
    shared_directory_count: Optional[int] = None
    country_code: Optional[str] = None
    
    @classmethod
    def from_api(cls, data: dict, username: str = None) -> "UserInfo":
        """Create UserInfo from slskd API response.
        
        Args:
            data: API response data
            username: Username (since API doesn't return it)
        """
        return cls(
            username=username or data.get("username", ""),
            description=data.get("description"),
            upload_slots=data.get("uploadSlots", 0),
            queue_length=data.get("queueLength", 0),
            has_free_slots=data.get("hasFreeUploadSlot", False),
            is_online=data.get("isOnline", False),
            shared_file_count=data.get("sharedFileCount"),
            shared_directory_count=data.get("sharedDirectoryCount"),
            country_code=data.get("countryCode")
        )


@dataclass
class Directory:
    """Represents a shared directory."""
    
    name: str
    files: List[File] = field(default_factory=list)
    
    @classmethod
    def from_api(cls, data: dict) -> "Directory":
        """Create Directory from slskd API response."""
        files = [File.from_api(f) for f in data.get("files", [])]
        return cls(
            name=data.get("name", ""),
            files=files
        )
    
    @property
    def file_count(self) -> int:
        """Get number of files in directory."""
        return len(self.files)
    
    @property
    def total_size(self) -> int:
        """Get total size of all files in bytes."""
        return sum(f.size for f in self.files)


@dataclass
class BrowseResult:
    """Result from browsing a user's shared files."""
    
    username: str
    directories: List[Directory] = field(default_factory=list)
    locked_directories: List[str] = field(default_factory=list)
    browse_time: Optional[datetime] = None
    
    @classmethod
    def from_api(cls, username: str, data: dict) -> "BrowseResult":
        """Create BrowseResult from slskd API response."""
        directories = [Directory.from_api(d) for d in data.get("directories", [])]
        locked = data.get("lockedDirectories", [])
        
        return cls(
            username=username,
            directories=directories,
            locked_directories=locked,
            browse_time=datetime.now()
        )
    
    @property
    def total_files(self) -> int:
        """Get total number of files."""
        return sum(d.file_count for d in self.directories)
    
    @property
    def total_size(self) -> int:
        """Get total size of all files."""
        return sum(d.total_size for d in self.directories)
    
    def get_all_files(self) -> List[File]:
        """Get all files from all directories."""
        all_files = []
        for directory in self.directories:
            all_files.extend(directory.files)
        return all_files
    
    def search_files(self, query: str) -> List[File]:
        """Search for files matching query."""
        query_lower = query.lower()
        matching = []
        
        for file in self.get_all_files():
            if query_lower in file.filename.lower():
                matching.append(file)
        
        return matching


@dataclass
class User:
    """Complete user model."""
    
    username: str
    info: Optional[UserInfo] = None
    browse_result: Optional[BrowseResult] = None
    last_seen: Optional[datetime] = None
    
    @property
    def is_online(self) -> bool:
        """Check if user is online."""
        return self.info.is_online if self.info else False
    
    @property
    def has_free_slots(self) -> bool:
        """Check if user has free upload slots."""
        return self.info.has_free_slots if self.info else False