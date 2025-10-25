"""
Google Calendar Integration Module
Handles fetching meetings from Google Calendar
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import Resource

class GoogleCalendarIntegration:
    """Handles Google Calendar operations"""
    
    def __init__(self, calendar_service: Resource):
        self.calendar_service = calendar_service
    
    def get_upcoming_meetings(self, months_back: int = 3) -> List[Dict[str, Any]]:
        """
        Fetch upcoming meetings from the past N months
        Args:
            months_back: Number of months to look back (default: 3)
        Returns:
            List of meeting dictionaries sorted by start time (latest first)
        """
        try:
            # Calculate time range
            now = datetime.utcnow()
            time_min = now - timedelta(days=months_back * 30)
            time_max = now + timedelta(days=30)  # Include some future meetings
            
            # Format times for API
            time_min_str = time_min.isoformat() + 'Z'
            time_max_str = time_max.isoformat() + 'Z'
            
            # Fetch events from primary calendar
            events_result = self.calendar_service.events().list(
                calendarId='primary',
                timeMin=time_min_str,
                timeMax=time_max_str,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Process and filter events
            meetings = []
            for event in events:
                meeting_info = self._extract_meeting_info(event)
                if meeting_info:
                    meetings.append(meeting_info)
            
            # Sort by start time (latest first)
            meetings.sort(key=lambda x: x['start_time'], reverse=True)
            
            return meetings
            
        except Exception as e:
            print(f"Error fetching calendar events: {e}")
            return []
    
    def _extract_meeting_info(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract relevant meeting information from calendar event
        Args:
            event: Calendar event dictionary
        Returns:
            Meeting info dictionary or None if not a valid meeting
        """
        try:
            # Check if event has Google Meet link
            meet_link = None
            if 'conferenceData' in event:
                conference_data = event['conferenceData']
                if 'entryPoints' in conference_data:
                    for entry_point in conference_data['entryPoints']:
                        if entry_point.get('entryPointType') == 'video':
                            meet_link = entry_point.get('uri')
                            break
            
            # Also check for meet links in description or location
            if not meet_link:
                description = event.get('description', '')
                location = event.get('location', '')
                
                # Look for meet.google.com links
                import re
                meet_pattern = r'https://meet\.google\.com/[a-z0-9-]+'
                
                for text in [description, location]:
                    match = re.search(meet_pattern, text)
                    if match:
                        meet_link = match.group()
                        break
            
            if not meet_link:
                return None
            
            # Extract start and end times
            start_time = None
            end_time = None
            
            if 'start' in event:
                start_data = event['start']
                if 'dateTime' in start_data:
                    start_time = datetime.fromisoformat(
                        start_data['dateTime'].replace('Z', '+00:00')
                    )
                elif 'date' in start_data:
                    start_time = datetime.fromisoformat(start_data['date'])
            
            if 'end' in event:
                end_data = event['end']
                if 'dateTime' in end_data:
                    end_time = datetime.fromisoformat(
                        end_data['dateTime'].replace('Z', '+00:00')
                    )
                elif 'date' in end_data:
                    end_time = datetime.fromisoformat(end_data['date'])
            
            return {
                'id': event.get('id'),
                'title': event.get('summary', 'No Title'),
                'description': event.get('description', ''),
                'start_time': start_time,
                'end_time': end_time,
                'meet_link': meet_link,
                'attendees': self._extract_attendees(event.get('attendees', [])),
                'organizer': event.get('organizer', {}).get('email', ''),
                'created': event.get('created'),
                'updated': event.get('updated')
            }
            
        except Exception as e:
            print(f"Error extracting meeting info: {e}")
            return None
    
    def _extract_attendees(self, attendees: List[Dict[str, Any]]) -> List[str]:
        """Extract attendee emails from event attendees"""
        return [attendee.get('email', '') for attendee in attendees if attendee.get('email')]
    
    def get_meeting_by_id(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific meeting details by ID
        Args:
            meeting_id: Calendar event ID
        Returns:
            Meeting info dictionary or None if not found
        """
        try:
            event = self.calendar_service.events().get(
                calendarId='primary',
                eventId=meeting_id
            ).execute()
            
            return self._extract_meeting_info(event)
            
        except Exception as e:
            print(f"Error fetching meeting by ID: {e}")
            return None
    
    def search_meetings_by_title(self, title_query: str, months_back: int = 3) -> List[Dict[str, Any]]:
        """
        Search for meetings by title
        Args:
            title_query: Search query for meeting title
            months_back: Number of months to look back
        Returns:
            List of matching meetings
        """
        try:
            # Calculate time range
            now = datetime.utcnow()
            time_min = now - timedelta(days=months_back * 30)
            time_max = now + timedelta(days=30)
            
            time_min_str = time_min.isoformat() + 'Z'
            time_max_str = time_max.isoformat() + 'Z'
            
            # Search for events with title query and meet links
            events_result = self.calendar_service.events().list(
                calendarId='primary',
                timeMin=time_min_str,
                timeMax=time_max_str,
                singleEvents=True,
                orderBy='startTime',
                q=f'{title_query} meet.google.com'
            ).execute()
            
            events = events_result.get('items', [])
            
            meetings = []
            for event in events:
                meeting_info = self._extract_meeting_info(event)
                if meeting_info:
                    meetings.append(meeting_info)
            
            meetings.sort(key=lambda x: x['start_time'], reverse=True)
            return meetings
            
        except Exception as e:
            print(f"Error searching meetings: {e}")
            return []
