"""
Charts API for Beatport.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from .base import BaseAPI
from ..models import Chart, ChartTrack, ChartType, Genre
from ..utils.parser import ResponseParser


class ChartsAPI(BaseAPI):
    """Handle chart operations."""
    
    def __init__(self, *args, **kwargs):
        """Initialize charts API."""
        super().__init__(*args, **kwargs)
        self.parser = ResponseParser()
    
    def get_chart(
        self,
        chart_type: ChartType = ChartType.TOP_100,
        genre_id: Optional[int] = None,
        time_period: str = "week"
    ) -> Chart:
        """
        Get chart by type and genre.
        
        Args:
            chart_type: Type of chart
            genre_id: Genre ID (None for all genres)
            time_period: Time period (week, month, all-time)
            
        Returns:
            Chart object
        """
        endpoint = f"charts/{chart_type.value}"
        
        params = {'time_period': time_period}
        if genre_id:
            params['genre_id'] = genre_id
        
        response = self.get(endpoint, params)
        return self.parser.parse_chart(response)
    
    def get_top_100(
        self,
        genre_id: Optional[int] = None
    ) -> List[ChartTrack]:
        """
        Get Beatport Top 100 chart.
        
        Args:
            genre_id: Genre ID (None for all genres)
            
        Returns:
            List of chart tracks
        """
        chart = self.get_chart(ChartType.TOP_100, genre_id)
        return chart.tracks
    
    def get_hype_chart(
        self,
        genre_id: Optional[int] = None
    ) -> List[ChartTrack]:
        """
        Get Hype chart (trending tracks).
        
        Args:
            genre_id: Genre ID (None for all genres)
            
        Returns:
            List of chart tracks
        """
        chart = self.get_chart(ChartType.HYPE, genre_id)
        return chart.tracks
    
    def get_essential_chart(
        self,
        genre_id: Optional[int] = None
    ) -> List[ChartTrack]:
        """
        Get Essential chart (curated picks).
        
        Args:
            genre_id: Genre ID (None for all genres)
            
        Returns:
            List of chart tracks
        """
        chart = self.get_chart(ChartType.ESSENTIAL, genre_id)
        return chart.tracks
    
    def get_beatport_picks(
        self,
        genre_id: Optional[int] = None
    ) -> List[ChartTrack]:
        """
        Get Beatport Picks chart.
        
        Args:
            genre_id: Genre ID (None for all genres)
            
        Returns:
            List of chart tracks
        """
        chart = self.get_chart(ChartType.BEATPORT_PICKS, genre_id)
        return chart.tracks
    
    def get_genre_charts(self, genre_id: int) -> Dict[str, Chart]:
        """
        Get all charts for a specific genre.
        
        Args:
            genre_id: Genre ID
            
        Returns:
            Dictionary of charts by type
        """
        charts = {}
        
        for chart_type in ChartType:
            try:
                chart = self.get_chart(chart_type, genre_id)
                charts[chart_type.value] = chart
            except:
                continue
        
        return charts
    
    def get_chart_history(
        self,
        chart_type: ChartType,
        genre_id: Optional[int] = None,
        weeks_back: int = 4
    ) -> List[Chart]:
        """
        Get historical chart data.
        
        Args:
            chart_type: Type of chart
            genre_id: Genre ID
            weeks_back: Number of weeks to go back
            
        Returns:
            List of historical charts
        """
        charts = []
        
        for week in range(weeks_back):
            endpoint = f"charts/{chart_type.value}/history"
            params = {'weeks_ago': week}
            if genre_id:
                params['genre_id'] = genre_id
            
            try:
                response = self.get(endpoint, params)
                chart = self.parser.parse_chart(response)
                charts.append(chart)
            except:
                continue
        
        return charts
    
    def get_dj_charts(
        self,
        dj_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get DJ charts.
        
        Args:
            dj_id: Specific DJ ID (None for all)
            limit: Maximum number of charts
            
        Returns:
            List of DJ charts
        """
        endpoint = "charts/dj"
        params = {'per_page': limit}
        
        if dj_id:
            params['dj_id'] = dj_id
        
        response = self.get(endpoint, params)
        return response.get('results', [])