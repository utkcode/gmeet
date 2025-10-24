"""
Google Drive Integration Module
Handles fetching meeting transcripts from Google Drive
"""

import os
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from googleapiclient.discovery import Resource
from googleapiclient.http import MediaIoBaseDownload
import io

class GoogleDriveIntegration:
    """Handles Google Drive operations for meeting transcripts"""
    
    def __init__(self, drive_service: Resource):
        self.drive_service = drive_service
        self.transcript_folder_name = "Meet Recordings"
    
    def search_meeting_transcripts(self, meeting_code: str = None, meeting_title: str = None, meeting_date: datetime = None) -> List[Dict[str, Any]]:
        """
        Search for meeting transcripts in Google Drive
        Args:
            meeting_code: Google Meet meeting code
            meeting_title: Meeting title to search for
            meeting_date: Meeting date for more precise search
        Returns:
            List of transcript files found
        """
        try:
            # First, try to find the "Meet Recordings" folder
            meet_recordings_folder = self._find_meet_recordings_folder()
            if not meet_recordings_folder:
                print("'Meet Recordings' folder not found in Google Drive")
                return []
            
            folder_id = meet_recordings_folder['id']
            print(f"Found 'Meet Recordings' folder: {meet_recordings_folder['name']}")
            
            # Search for files in the Meet Recordings folder
            query_parts = [f"'{folder_id}' in parents"]
            
            # Add meeting-specific search terms
            if meeting_title:
                # Clean title for search (remove special characters)
                clean_title = re.sub(r'[^\w\s]', '', meeting_title)
                query_parts.append(f"name contains '{clean_title}'")
            
            # Search for transcript files with specific naming pattern
            transcript_query = "name contains 'Transcript'"
            query_parts.append(transcript_query)
            
            # Note: We don't search for meeting code in filename as Google Meet 
            # transcript files don't include meeting codes in their names
            
            full_query = " and ".join(query_parts)
            print(f"Search query: {full_query}")
            
            # Execute search
            results = self.drive_service.files().list(
                q=full_query,
                fields="files(id, name, mimeType, size, createdTime, modifiedTime, parents, webViewLink)"
            ).execute()
            
            files = results.get('files', [])
            print(f"Found {len(files)} files matching search criteria")
            
            # Process and filter files
            transcript_files = []
            for file in files:
                transcript_info = self._extract_transcript_info(file)
                if transcript_info:
                    transcript_files.append(transcript_info)
                    print(f"Valid transcript: {transcript_info['name']}")
            
            return transcript_files
            
        except Exception as e:
            print(f"Error searching for transcripts: {e}")
            return []
    
    def _find_meet_recordings_folder(self) -> Optional[Dict[str, Any]]:
        """
        Find the 'Meet Recordings' folder in Google Drive
        Returns:
            Folder info dictionary or None if not found
        """
        try:
            # Search for the Meet Recordings folder
            query = "name = 'Meet Recordings' and mimeType = 'application/vnd.google-apps.folder'"
            
            results = self.drive_service.files().list(
                q=query,
                fields="files(id, name, mimeType, parents)"
            ).execute()
            
            folders = results.get('files', [])
            
            if folders:
                return folders[0]  # Return the first match
            else:
                # Try alternative names
                alternative_names = [
                    "Meet recordings",
                    "Google Meet Recordings", 
                    "Meeting Recordings",
                    "Recordings"
                ]
                
                for alt_name in alternative_names:
                    query = f"name contains '{alt_name}' and mimeType = 'application/vnd.google-apps.folder'"
                    results = self.drive_service.files().list(q=query).execute()
                    folders = results.get('files', [])
                    if folders:
                        print(f"Found folder with alternative name: {folders[0]['name']}")
                        return folders[0]
                
                return None
                
        except Exception as e:
            print(f"Error finding Meet Recordings folder: {e}")
            return None
    
    def _extract_transcript_info(self, file: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract relevant information from transcript file
        Args:
            file: Google Drive file dictionary
        Returns:
            Transcript info dictionary or None if not a valid transcript
        """
        try:
            name = file.get('name', '').lower()
            mime_type = file.get('mimeType', '')
            
            # Check if it's a transcript file based on the naming convention
            # Format: [Meeting name] ([Date and time of meeting]) - Transcript
            is_transcript = (
                'transcript' in name or
                name.endswith(' - transcript') or
                name.endswith(' - Transcript') or
                'transcript' in mime_type.lower()
            )
            
            if not is_transcript:
                return None
            
            # Extract meeting code from filename if possible
            meeting_code = self._extract_meeting_code_from_filename(file.get('name', ''))
            
            # Extract meeting title and date from filename
            meeting_title, meeting_date = self._parse_transcript_filename(file.get('name', ''))
            
            return {
                'file_id': file.get('id'),
                'name': file.get('name'),
                'mime_type': mime_type,
                'size': file.get('size'),
                'created_time': file.get('createdTime'),
                'modified_time': file.get('modifiedTime'),
                'web_view_link': file.get('webViewLink'),
                'meeting_code': meeting_code,
                'meeting_title': meeting_title,
                'meeting_date': meeting_date,
                'is_transcript': True
            }
            
        except Exception as e:
            print(f"Error extracting transcript info: {e}")
            return None
    
    def _parse_transcript_filename(self, filename: str) -> tuple[Optional[str], Optional[str]]:
        """
        Parse transcript filename to extract meeting title and date
        Format: [Meeting name] ([Date and time of meeting]) - Transcript
        Args:
            filename: Name of the transcript file
        Returns:
            Tuple of (meeting_title, meeting_date) or (None, None) if parsing fails
        """
        try:
            # Remove the " - Transcript" suffix
            if filename.endswith(' - Transcript'):
                filename = filename[:-12]  # Remove " - Transcript"
            elif filename.endswith(' - transcript'):
                filename = filename[:-12]  # Remove " - transcript"
            
            # Look for pattern: Meeting name (Date and time)
            import re
            pattern = r'^(.+?)\s*\((.+?)\)$'
            match = re.match(pattern, filename)
            
            if match:
                meeting_title = match.group(1).strip()
                meeting_date = match.group(2).strip()
                return meeting_title, meeting_date
            else:
                # If no parentheses found, treat entire filename as title
                return filename.strip(), None
                
        except Exception as e:
            print(f"Error parsing transcript filename: {e}")
            return None, None
    
    def _extract_meeting_code_from_filename(self, filename: str) -> Optional[str]:
        """
        Extract meeting code from filename
        Args:
            filename: Name of the file
        Returns:
            Meeting code if found, None otherwise
        """
        # Look for patterns like meeting codes in filenames
        patterns = [
            r'([a-z0-9]{3}-[a-z0-9]{4}-[a-z0-9]{3})',  # Standard meet code format
            r'([a-z0-9-]{10,})',  # General meet code pattern
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename.lower())
            if match:
                return match.group(1)
        
        return None
    
    def download_transcript(self, file_id: str, output_path: str = None) -> Optional[str]:
        """
        Download transcript file from Google Drive
        Args:
            file_id: Google Drive file ID
            output_path: Local path to save the file
        Returns:
            Path to downloaded file or None if failed
        """
        try:
            # Get file metadata
            file_metadata = self.drive_service.files().get(fileId=file_id).execute()
            filename = file_metadata.get('name', 'transcript.txt')
            mime_type = file_metadata.get('mimeType', '')
            
            print(f"File: {filename}")
            print(f"MIME Type: {mime_type}")
            
            # Set output path if not provided
            if not output_path:
                output_path = f"transcripts/{filename}"
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Handle different file types
            if mime_type == 'application/vnd.google-apps.document':
                # Google Docs - export as DOCX
                print("Exporting Google Doc as DOCX...")
                request = self.drive_service.files().export_media(
                    fileId=file_id,
                    mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                )
            elif filename.endswith('.docx') or 'docx' in mime_type:
                # Already a DOCX file - download directly
                print("Downloading DOCX file...")
                request = self.drive_service.files().get_media(fileId=file_id)
            else:
                # Other file types - download as is
                print("Downloading file...")
                request = self.drive_service.files().get_media(fileId=file_id)
            
            # Download file
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            # Save to file
            with open(output_path, 'wb') as f:
                f.write(fh.getvalue())
            
            print(f"Transcript downloaded to: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error downloading transcript: {e}")
            return None
    
    def get_transcript_content(self, file_id: str) -> Optional[str]:
        """
        Get transcript content as text
        Args:
            file_id: Google Drive file ID
        Returns:
            Transcript content as string or None if failed
        """
        try:
            # Get file metadata
            file_metadata = self.drive_service.files().get(fileId=file_id).execute()
            mime_type = file_metadata.get('mimeType', '')
            filename = file_metadata.get('name', '')
            
            print(f"Getting content from: {filename}")
            print(f"MIME Type: {mime_type}")
            
            # Handle Google Docs
            if mime_type == 'application/vnd.google-apps.document':
                print("Exporting Google Doc as plain text...")
                request = self.drive_service.files().export_media(
                    fileId=file_id,
                    mimeType='text/plain'
                )
                content = request.execute()
                return content.decode('utf-8')
            
            # Handle DOCX files
            elif filename.endswith('.docx') or 'docx' in mime_type:
                print("DOCX file detected - downloading for content extraction...")
                # For DOCX files, we need to download and extract text
                temp_path = self.download_transcript(file_id, f"transcripts/temp_{file_id}.docx")
                if temp_path and os.path.exists(temp_path):
                    try:
                        # Try to read DOCX content using python-docx if available
                        try:
                            from docx import Document
                            doc = Document(temp_path)
                            content = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                            return content
                        except ImportError:
                            print("python-docx not available, trying basic text extraction...")
                            # Fallback: try to read as text (may not work well)
                            with open(temp_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                            return content
                    except Exception as e:
                        print(f"Error extracting DOCX content: {e}")
                        return None
                    finally:
                        # Always clean up temp file
                        try:
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                                print(f"Cleaned up temp file: {temp_path}")
                        except Exception as cleanup_error:
                            print(f"Warning: Could not clean up temp file: {cleanup_error}")
                else:
                    print("Failed to download temp file for content extraction")
                    return None
            
            # Handle text files
            elif 'text' in mime_type or filename.endswith('.txt'):
                print("Getting text content...")
                request = self.drive_service.files().get_media(fileId=file_id)
                content = request.execute()
                return content.decode('utf-8')
            
            # For other file types, try to download and read
            else:
                print("Downloading file for content extraction...")
                temp_path = self.download_transcript(file_id, f"transcripts/temp_{file_id}")
                if temp_path and os.path.exists(temp_path):
                    try:
                        with open(temp_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        return content
                    except UnicodeDecodeError:
                        # Try different encodings
                        for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                            try:
                                with open(temp_path, 'r', encoding=encoding) as f:
                                    content = f.read()
                                return content
                            except:
                                continue
                        return None
                    finally:
                        # Always clean up temp file
                        try:
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                                print(f"Cleaned up temp file: {temp_path}")
                        except Exception as cleanup_error:
                            print(f"Warning: Could not clean up temp file: {cleanup_error}")
            
            return None
            
        except Exception as e:
            print(f"Error getting transcript content: {e}")
            return None
    
    def search_transcripts_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Search for transcripts within a date range
        Args:
            start_date: Start date for search
            end_date: End date for search
        Returns:
            List of transcript files in date range
        """
        try:
            # Format dates for Google Drive API
            start_str = start_date.isoformat() + 'Z'
            end_str = end_date.isoformat() + 'Z'
            
            query = f"modifiedTime >= '{start_str}' and modifiedTime <= '{end_str}' and (name contains 'transcript' or name contains 'Transcript')"
            
            results = self.drive_service.files().list(
                q=query,
                fields="files(id, name, mimeType, size, createdTime, modifiedTime, parents, webViewLink)"
            ).execute()
            
            files = results.get('files', [])
            
            transcript_files = []
            for file in files:
                transcript_info = self._extract_transcript_info(file)
                if transcript_info:
                    transcript_files.append(transcript_info)
            
            return transcript_files
            
        except Exception as e:
            print(f"Error searching transcripts by date: {e}")
            return []
    
    def get_folder_contents(self, folder_name: str = "Meet Recordings") -> List[Dict[str, Any]]:
        """
        Get contents of a specific folder
        Args:
            folder_name: Name of the folder to search
        Returns:
            List of files in the folder
        """
        try:
            # First, find the folder
            folder_query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder'"
            folder_results = self.drive_service.files().list(q=folder_query).execute()
            
            folders = folder_results.get('files', [])
            if not folders:
                print(f"Folder '{folder_name}' not found")
                return []
            
            folder_id = folders[0]['id']
            
            # Get files in the folder
            files_query = f"'{folder_id}' in parents"
            files_results = self.drive_service.files().list(
                q=files_query,
                fields="files(id, name, mimeType, size, createdTime, modifiedTime, parents, webViewLink)"
            ).execute()
            
            files = files_results.get('files', [])
            
            transcript_files = []
            for file in files:
                transcript_info = self._extract_transcript_info(file)
                if transcript_info:
                    transcript_files.append(transcript_info)
            
            return transcript_files
            
        except Exception as e:
            print(f"Error getting folder contents: {e}")
            return []
