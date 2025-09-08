"""
File-related models for Soulseek.
"""

from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass
class File:
    """Represents a file in Soulseek network."""
    
    filename: str
    size: int
    extension: Optional[str] = None
    bitrate: Optional[int] = None
    sample_rate: Optional[int] = None
    length: Optional[int] = None  # Duration in seconds
    
    def __post_init__(self):
        """Post-initialization processing."""
        if not self.extension and self.filename:
            self.extension = Path(self.filename).suffix
    
    @classmethod
    def from_api(cls, data: dict) -> "File":
        """Create File from slskd API response."""
        return cls(
            filename=data.get("filename", ""),
            size=data.get("size", 0),
            extension=data.get("extension") or Path(data.get("filename", "")).suffix,
            bitrate=data.get("bitRate"),
            sample_rate=data.get("sampleRate"),
            length=data.get("length")
        )
    
    @property
    def name(self) -> str:
        """Get just the filename without path."""
        return Path(self.filename).name
    
    @property
    def is_lossless(self) -> bool:
        """Check if file appears to be lossless format."""
        lossless_extensions = {".flac", ".wav", ".aiff", ".alac", ".ape"}
        return self.extension.lower() in lossless_extensions if self.extension else False
    
    @property
    def size_mb(self) -> float:
        """Get file size in megabytes."""
        return self.size / (1024 * 1024) if self.size else 0


@dataclass
class FileInfo:
    """Extended file information with user context."""
    
    file: File
    username: str
    free_upload_slots: bool = False
    upload_speed: Optional[int] = None
    queue_length: int = 0
    user_directory: Optional[str] = None
    
    @classmethod
    def from_search_result(cls, file_data: dict, response_data: dict) -> "FileInfo":
        """Create FileInfo from search response."""
        return cls(
            file=File.from_api(file_data),
            username=response_data.get("username", ""),
            free_upload_slots=response_data.get("hasFreeUploadSlot", False),
            upload_speed=response_data.get("uploadSpeed"),
            queue_length=response_data.get("queueLength", 0)
        )
    
    @property
    def quality_score(self) -> float:
        """Calculate a quality score for ranking results."""
        score = 0.0
        
        # Bitrate score (max 40 points)
        if self.file.bitrate:
            score += min(40, self.file.bitrate / 8)
        elif self.file.is_lossless:
            score += 40
        
        # Availability score (max 30 points)
        if self.free_upload_slots:
            score += 30
        elif self.queue_length < 5:
            score += 20
        elif self.queue_length < 10:
            score += 10
        
        # Upload speed score (max 20 points)
        if self.upload_speed:
            score += min(20, self.upload_speed / 50000)
        
        # File size score (max 10 points, prefer larger files)
        score += min(10, self.file.size_mb / 10)
        
        return score