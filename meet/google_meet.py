"""
Google Meet Integration Module
Handles Google Meet meeting details and URL parsing
"""

import re
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs

class GoogleMeetIntegration:
    """Handles Google Meet operations and URL parsing"""
    
    def __init__(self):
        self.meet_pattern = re.compile(r'https://meet\.google\.com/([a-z0-9-]+)')
    
    def parse_meet_url(self, meet_url: str) -> Optional[Dict[str, Any]]:
        """
        Parse Google Meet URL to extract meeting code
        Args:
            meet_url: Google Meet URL
        Returns:
            Dictionary with meeting details or None if invalid
        """
        try:
            # Clean the URL
            meet_url = meet_url.strip()
            
            # Extract meeting code using regex
            match = self.meet_pattern.search(meet_url)
            if not match:
                return None
            
            meeting_code = match.group(1)
            
            # Parse URL for additional parameters
            parsed_url = urlparse(meet_url)
            query_params = parse_qs(parsed_url.query)
            
            return {
                'meeting_code': meeting_code,
                'meeting_url': meet_url,
                'meeting_id': meeting_code,
                'query_params': query_params,
                'is_valid': True
            }
            
        except Exception as e:
            print(f"Error parsing Meet URL: {e}")
            return None
    
    def validate_meet_url(self, meet_url: str) -> bool:
        """
        Validate if the provided URL is a valid Google Meet URL
        Args:
            meet_url: URL to validate
        Returns:
            True if valid, False otherwise
        """
        parsed = self.parse_meet_url(meet_url)
        return parsed is not None and parsed.get('is_valid', False)
    
    def extract_meeting_code_from_url(self, meet_url: str) -> Optional[str]:
        """
        Extract meeting code from Google Meet URL
        Args:
            meet_url: Google Meet URL
        Returns:
            Meeting code or None if not found
        """
        parsed = self.parse_meet_url(meet_url)
        return parsed.get('meeting_code') if parsed else None
    
    def format_meet_url(self, meeting_code: str) -> str:
        """
        Format meeting code into proper Google Meet URL
        Args:
            meeting_code: Meeting code
        Returns:
            Formatted Google Meet URL
        """
        return f"https://meet.google.com/{meeting_code}"
    
    def get_meeting_info_from_url(self, meet_url: str) -> Dict[str, Any]:
        """
        Get comprehensive meeting information from URL
        Args:
            meet_url: Google Meet URL
        Returns:
            Dictionary with meeting information
        """
        parsed = self.parse_meet_url(meet_url)
        if not parsed:
            return {
                'is_valid': False,
                'error': 'Invalid Google Meet URL'
            }
        
        return {
            'is_valid': True,
            'meeting_code': parsed['meeting_code'],
            'meeting_url': parsed['meeting_url'],
            'meeting_id': parsed['meeting_id'],
            'formatted_url': self.format_meet_url(parsed['meeting_code']),
            'query_params': parsed['query_params']
        }
    
    def search_meet_urls_in_text(self, text: str) -> list[str]:
        """
        Search for Google Meet URLs in text content
        Args:
            text: Text content to search
        Returns:
            List of found Google Meet URLs
        """
        matches = self.meet_pattern.findall(text)
        return [self.format_meet_url(match) for match in matches]
    
    def is_meet_url(self, url: str) -> bool:
        """
        Check if URL is a Google Meet URL
        Args:
            url: URL to check
        Returns:
            True if it's a Google Meet URL
        """
        return bool(self.meet_pattern.search(url))
