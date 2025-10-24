"""
Main Script for Google Meet Transcript Downloader
Handles user interaction and orchestrates the integration modules
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from google_auth import GoogleAuthManager
from google_calendar import GoogleCalendarIntegration
from google_meet import GoogleMeetIntegration
from google_drive import GoogleDriveIntegration

class MeetTranscriptDownloader:
    """Main class for handling meeting transcript downloads"""
    
    def __init__(self):
        self.auth_manager = GoogleAuthManager()
        self.calendar_integration = None
        self.meet_integration = GoogleMeetIntegration()
        self.drive_integration = None
        self.is_authenticated = False
    
    def initialize(self) -> bool:
        """
        Initialize the application and authenticate with Google APIs
        Returns:
            True if initialization successful, False otherwise
        """
        print("Authenticating with Google APIs...")
        
        if not self.auth_manager.authenticate():
            print("Authentication failed. Please check your credentials.")
            return False
        
        self.is_authenticated = True
        self.calendar_integration = GoogleCalendarIntegration(
            self.auth_manager.get_calendar_service()
        )
        self.drive_integration = GoogleDriveIntegration(
            self.auth_manager.get_drive_service()
        )
        
        print("Successfully authenticated with Google APIs!")
        return True
    
    def run(self):
        """Main application loop"""
        if not self.initialize():
            return
        
        print("\n" + "="*60)
        print("Google Meet Transcript Downloader")
        print("="*60)
        
        while True:
            try:
                self.show_main_menu()
                choice = input("\nEnter your choice (1-3): ").strip()
                
                if choice == '1':
                    self.handle_calendar_integration()
                elif choice == '2':
                    self.handle_direct_meeting_input()
                elif choice == '3':
                    print("Goodbye!")
                    break
                else:
                    print("Invalid choice. Please try again.")
                    
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                print("Please try again.")
    
    def show_main_menu(self):
        """Display the main menu"""
        print("\nMain Menu:")
        print("1. Integrate with Google Calendar")
        print("2. Enter meeting details directly")
        print("3. Exit")
    
    def handle_calendar_integration(self):
        """Handle calendar integration workflow"""
        print("\nFetching meetings from Google Calendar...")
        
        # Get meetings from the past 3 months
        meetings = self.calendar_integration.get_upcoming_meetings(months_back=3)
        
        if not meetings:
            print("No Google Meet meetings found in your calendar.")
            return
        
        print(f"\nFound {len(meetings)} Google Meet meetings:")
        self.display_meetings(meetings)
        
        # Let user select a meeting
        selected_meeting = self.select_meeting(meetings)
        if not selected_meeting:
            return
        
        # Process the selected meeting
        self.process_meeting(selected_meeting)
    
    def handle_direct_meeting_input(self):
        """Handle direct meeting input workflow"""
        print("\nDirect Meeting Input")
        print("Enter Google Meet URL or meeting details:")
        
        meet_url = input("Google Meet URL: ").strip()
        
        if not meet_url:
            print("No URL provided.")
            return
        
        # Validate and parse the URL
        meet_info = self.meet_integration.get_meeting_info_from_url(meet_url)
        
        if not meet_info['is_valid']:
            print(f"Invalid Google Meet URL: {meet_info.get('error', 'Unknown error')}")
            return
        
        print(f"Valid Google Meet URL detected!")
        print(f"   Meeting Code: {meet_info['meeting_code']}")
        
        # Create a mock meeting object for processing
        meeting_data = {
            'id': meet_info['meeting_id'],
            'title': f"Meeting {meet_info['meeting_code']}",
            'description': '',
            'start_time': datetime.now(),
            'end_time': datetime.now() + timedelta(hours=1),
            'meet_link': meet_info['meeting_url'],
            'attendees': [],
            'organizer': '',
            'created': datetime.now().isoformat(),
            'updated': datetime.now().isoformat()
        }
        
        self.process_meeting(meeting_data)
    
    def display_meetings(self, meetings: List[Dict[str, Any]]):
        """Display list of meetings"""
        for i, meeting in enumerate(meetings, 1):
            start_time = meeting['start_time'].strftime("%Y-%m-%d %H:%M") if meeting['start_time'] else "Unknown"
            print(f"{i:2d}. {meeting['title']}")
            print(f"    Date: {start_time}")
            print(f"    URL: {meeting['meet_link']}")
            if meeting['attendees']:
                print(f"    Attendees: {len(meeting['attendees'])}")
            print()
    
    def select_meeting(self, meetings: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Let user select a meeting from the list"""
        while True:
            try:
                choice = input(f"Select a meeting (1-{len(meetings)}) or 'q' to quit: ").strip()
                
                if choice.lower() == 'q':
                    return None
                
                index = int(choice) - 1
                if 0 <= index < len(meetings):
                    return meetings[index]
                else:
                    print(f"Please enter a number between 1 and {len(meetings)}")
                    
            except ValueError:
                print("Please enter a valid number or 'q' to quit")
    
    def process_meeting(self, meeting: Dict[str, Any]):
        """Process a selected meeting to download its transcript"""
        print(f"\nProcessing meeting: {meeting['title']}")
        print(f"Meeting URL: {meeting['meet_link']}")
        
        # Extract meeting code from URL
        meeting_code = self.meet_integration.extract_meeting_code_from_url(meeting['meet_link'])
        
        if not meeting_code:
            print("Could not extract meeting code from URL")
            return
        
        print(f"Searching for transcripts with meeting code: {meeting_code}")
        
        # Search for transcripts
        transcripts = self.drive_integration.search_meeting_transcripts(
            meeting_code=meeting_code,
            meeting_title=meeting['title'],
            meeting_date=meeting['start_time']
        )
        
        if not transcripts:
            print("No transcripts found for this meeting.")
            print("Make sure the meeting was recorded and transcripts are available in Google Drive.")
            return
        
        print(f"Found {len(transcripts)} transcript file(s):")
        self.display_transcripts(transcripts)
        
        # Let user select transcript to download
        selected_transcript = self.select_transcript(transcripts)
        if not selected_transcript:
            return
        
        # Download the transcript
        self.download_transcript(selected_transcript, meeting)
    
    def display_transcripts(self, transcripts: List[Dict[str, Any]]):
        """Display list of available transcripts"""
        for i, transcript in enumerate(transcripts, 1):
            size_mb = int(transcript['size']) / (1024 * 1024) if transcript['size'] else 0
            modified = datetime.fromisoformat(transcript['modified_time'].replace('Z', '+00:00'))
            modified_str = modified.strftime("%Y-%m-%d %H:%M")
            
            print(f"{i:2d}. {transcript['name']}")
            print(f"    Size: {size_mb:.1f} MB")
            print(f"    Modified: {modified_str}")
            if transcript.get('meeting_title'):
                print(f"    Meeting: {transcript['meeting_title']}")
            if transcript.get('meeting_date'):
                print(f"    Date: {transcript['meeting_date']}")
            if transcript['meeting_code']:
                print(f"    Meeting Code: {transcript['meeting_code']}")
            print()
    
    def select_transcript(self, transcripts: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Let user select a transcript to download"""
        while True:
            try:
                choice = input(f"Select a transcript to download (1-{len(transcripts)}) or 'q' to quit: ").strip()
                
                if choice.lower() == 'q':
                    return None
                
                index = int(choice) - 1
                if 0 <= index < len(transcripts):
                    return transcripts[index]
                else:
                    print(f"Please enter a number between 1 and {len(transcripts)}")
                    
            except ValueError:
                print("Please enter a valid number or 'q' to quit")
    
    def download_transcript(self, transcript: Dict[str, Any], meeting: Dict[str, Any]):
        """Download the selected transcript"""
        print(f"\nDownloading transcript: {transcript['name']}")
        
        # Create a clean, short filename
        meeting_date = meeting['start_time'].strftime("%Y%m%d_%H%M") if meeting['start_time'] else "unknown_date"
        meeting_title = self.sanitize_filename(meeting['title'])
        
        # Create a short filename to avoid Windows path length issues
        filename = f"{meeting_date}_{meeting_title}_transcript.docx"
        output_path = f"transcripts/{filename}"
        
        # Download the file
        downloaded_path = self.drive_integration.download_transcript(
            transcript['file_id'], 
            output_path
        )
        
        if downloaded_path:
            print(f"Transcript successfully downloaded to: {downloaded_path}")
            
            # Also get the content for preview
            content = self.drive_integration.get_transcript_content(transcript['file_id'])
            if content:
                preview_length = min(500, len(content))
                print(f"\nPreview of transcript (first {preview_length} characters):")
                print("-" * 50)
                print(content[:preview_length])
                if len(content) > preview_length:
                    print("...")
                print("-" * 50)
        else:
            print("Failed to download transcript")
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility"""
        import re
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove extra spaces and limit length
        filename = re.sub(r'\s+', '_', filename.strip())
        return filename[:100]  # Increased limit to 100 characters

def main():
    """Main entry point"""
    print("Starting Google Meet Transcript Downloader...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print(".env file not found!")
        print("Please create a .env file with your Google API credentials.")
        print("Use env_template.txt as a reference.")
        return
    
    # Create transcripts directory
    os.makedirs('transcripts', exist_ok=True)
    
    # Run the application
    app = MeetTranscriptDownloader()
    app.run()

if __name__ == "__main__":
    main()
