"""
Search-related models for Soulseek.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

from .file import FileInfo


class SearchState(Enum):
    """Search operation states."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class SearchResponse:
    """Response from a single user for a search."""
    
    username: str
    files: List[FileInfo] = field(default_factory=list)
    has_free_upload_slot: bool = False
    upload_speed: Optional[int] = None
    queue_length: int = 0
    response_time: Optional[float] = None
    
    @classmethod
    def from_api(cls, data: dict) -> "SearchResponse":
        """Create SearchResponse from slskd API response."""
        username = data.get("username", "")
        files = []
        
        for file_data in data.get("files", []):
            file_info = FileInfo.from_search_result(file_data, data)
            files.append(file_info)
        
        return cls(
            username=username,
            files=files,
            has_free_upload_slot=data.get("hasFreeUploadSlot", False),
            upload_speed=data.get("uploadSpeed"),
            queue_length=data.get("queueLength", 0),
            response_time=data.get("responseTime")
        )


@dataclass
class SearchResult:
    """Complete search result with all responses."""
    
    search_id: str
    query: str
    state: SearchState
    responses: List[SearchResponse] = field(default_factory=list)
    file_count: int = 0
    response_count: int = 0
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @classmethod
    def from_api(cls, search_data: dict, responses: List[dict]) -> "SearchResult":
        """Create SearchResult from slskd API data."""
        search_responses = [SearchResponse.from_api(r) for r in responses]
        
        # Count total files
        file_count = sum(len(r.files) for r in search_responses)
        
        return cls(
            search_id=search_data.get("id", ""),
            query=search_data.get("searchText", ""),
            state=SearchState(search_data.get("state", "pending").lower()),
            responses=search_responses,
            file_count=file_count,
            response_count=len(search_responses)
        )
    
    def get_all_files(self) -> List[FileInfo]:
        """Get all files from all responses."""
        all_files = []
        for response in self.responses:
            all_files.extend(response.files)
        return all_files
    
    def get_best_files(self, limit: int = 50) -> List[FileInfo]:
        """Get best files sorted by quality score."""
        all_files = self.get_all_files()
        
        # Sort by quality score
        all_files.sort(key=lambda f: f.quality_score, reverse=True)
        
        return all_files[:limit]
    
    def filter_by_bitrate(self, min_bitrate: int) -> List[FileInfo]:
        """Filter files by minimum bitrate."""
        filtered = []
        for file_info in self.get_all_files():
            if file_info.file.bitrate:
                if file_info.file.bitrate >= min_bitrate:
                    filtered.append(file_info)
            elif file_info.file.is_lossless:
                # Include lossless files regardless of bitrate
                filtered.append(file_info)
        return filtered