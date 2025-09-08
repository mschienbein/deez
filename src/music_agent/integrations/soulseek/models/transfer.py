"""
Transfer-related models for Soulseek.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum
from datetime import datetime


class TransferState(Enum):
    """Transfer states."""
    QUEUED = "queued"
    INITIALIZING = "initializing"
    IN_PROGRESS = "inprogress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    ABORTED = "aborted"


class TransferDirection(Enum):
    """Transfer direction."""
    DOWNLOAD = "download"
    UPLOAD = "upload"


@dataclass
class Transfer:
    """Represents a file transfer."""
    
    id: str
    username: str
    filename: str
    direction: TransferDirection
    state: TransferState
    size: int
    bytes_transferred: int = 0
    average_speed: Optional[float] = None
    percent_complete: float = 0.0
    remaining_time: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    @classmethod
    def from_api(cls, data: dict) -> "Transfer":
        """Create Transfer from slskd API response."""
        direction = TransferDirection.DOWNLOAD if data.get("direction", "").lower() == "download" else TransferDirection.UPLOAD
        
        # Parse state
        state_str = data.get("state", "queued").lower()
        state_map = {
            "queued": TransferState.QUEUED,
            "initializing": TransferState.INITIALIZING,
            "inprogress": TransferState.IN_PROGRESS,
            "in_progress": TransferState.IN_PROGRESS,
            "completed": TransferState.COMPLETED,
            "succeeded": TransferState.COMPLETED,
            "failed": TransferState.FAILED,
            "cancelled": TransferState.CANCELLED,
            "rejected": TransferState.REJECTED,
            "aborted": TransferState.ABORTED
        }
        state = state_map.get(state_str, TransferState.QUEUED)
        
        return cls(
            id=data.get("id", ""),
            username=data.get("username", ""),
            filename=data.get("filename", ""),
            direction=direction,
            state=state,
            size=data.get("size", 0),
            bytes_transferred=data.get("bytesTransferred", 0),
            average_speed=data.get("averageSpeed"),
            percent_complete=data.get("percentComplete", 0.0),
            remaining_time=data.get("remainingTime"),
            error_message=data.get("errorMessage")
        )
    
    @property
    def is_complete(self) -> bool:
        """Check if transfer is complete."""
        return self.state == TransferState.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Check if transfer failed."""
        return self.state in [TransferState.FAILED, TransferState.CANCELLED, 
                             TransferState.REJECTED, TransferState.ABORTED]
    
    @property
    def is_active(self) -> bool:
        """Check if transfer is active."""
        return self.state in [TransferState.IN_PROGRESS, TransferState.INITIALIZING]
    
    @property
    def size_mb(self) -> float:
        """Get size in megabytes."""
        return self.size / (1024 * 1024) if self.size else 0
    
    @property
    def transferred_mb(self) -> float:
        """Get transferred bytes in megabytes."""
        return self.bytes_transferred / (1024 * 1024) if self.bytes_transferred else 0
    
    @property
    def speed_mbps(self) -> float:
        """Get speed in MB/s."""
        return self.average_speed / (1024 * 1024) if self.average_speed else 0