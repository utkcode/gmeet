"""
Flask API Server for Google Meet Transcript Downloader
Provides REST API endpoints for the React frontend
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json

from google_auth import GoogleAuthManager
from google_calendar import GoogleCalendarIntegration
from google_meet import GoogleMeetIntegration
from google_drive import GoogleDriveIntegration

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Global instances
auth_manager = None
calendar_integration = None
meet_integration = None
drive_integration = None
is_authenticated = False

def initialize_backend():
    """Initialize the backend services"""
    global auth_manager, calendar_integration, meet_integration, drive_integration, is_authenticated
    
    try:
        auth_manager = GoogleAuthManager()
        meet_integration = GoogleMeetIntegration()
        
        if auth_manager.authenticate():
            calendar_integration = GoogleCalendarIntegration(
                auth_manager.get_calendar_service()
            )
            drive_integration = GoogleDriveIntegration(
                auth_manager.get_drive_service()
            )
            is_authenticated = True
            return True
        else:
            return False
    except Exception as e:
        print(f"Error initializing backend: {e}")
        return False

@app.route('/api/auth/status', methods=['GET'])
def get_auth_status():
    """Check authentication status"""
    global is_authenticated
    return jsonify({
        'authenticated': is_authenticated,
        'message': 'Authenticated' if is_authenticated else 'Not authenticated'
    })

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Initiate Google authentication"""
    global is_authenticated
    
    try:
        if not is_authenticated:
            success = initialize_backend()
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Successfully authenticated with Google'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to authenticate with Google'
                }), 401
        else:
            return jsonify({
                'success': True,
                'message': 'Already authenticated'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Authentication error: {str(e)}'
        }), 500

@app.route('/api/meetings', methods=['GET'])
def get_meetings():
    """Get list of meetings from Google Calendar"""
    global calendar_integration, is_authenticated
    
    if not is_authenticated or not calendar_integration:
        return jsonify({
            'success': False,
            'message': 'Not authenticated'
        }), 401
    
    try:
        # Get meetings from the past 3 months
        meetings = calendar_integration.get_upcoming_meetings(months_back=3)
        
        # Convert datetime objects to strings for JSON serialization
        serialized_meetings = []
        for meeting in meetings:
            serialized_meeting = meeting.copy()
            if meeting['start_time']:
                serialized_meeting['start_time'] = meeting['start_time'].isoformat()
            if meeting['end_time']:
                serialized_meeting['end_time'] = meeting['end_time'].isoformat()
            serialized_meetings.append(serialized_meeting)
        
        return jsonify({
            'success': True,
            'meetings': serialized_meetings,
            'count': len(serialized_meetings)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching meetings: {str(e)}'
        }), 500

@app.route('/api/meetings/<meeting_id>/transcripts', methods=['GET'])
def get_meeting_transcripts(meeting_id):
    """Get available transcripts for a specific meeting"""
    global calendar_integration, meet_integration, drive_integration, is_authenticated
    
    if not is_authenticated or not all([calendar_integration, meet_integration, drive_integration]):
        return jsonify({
            'success': False,
            'message': 'Not authenticated'
        }), 401
    
    try:
        # Get meeting details
        meeting = calendar_integration.get_meeting_by_id(meeting_id)
        if not meeting:
            return jsonify({
                'success': False,
                'message': 'Meeting not found'
            }), 404
        
        # Extract meeting code from URL
        meeting_code = meet_integration.extract_meeting_code_from_url(meeting['meet_link'])
        if not meeting_code:
            return jsonify({
                'success': False,
                'message': 'Could not extract meeting code from URL'
            }), 400
        
        # Search for transcripts
        transcripts = drive_integration.search_meeting_transcripts(
            meeting_code=meeting_code,
            meeting_title=meeting['title'],
            meeting_date=meeting['start_time']
        )
        
        # Serialize transcript data
        serialized_transcripts = []
        for transcript in transcripts:
            serialized_transcript = transcript.copy()
            if transcript.get('meeting_date'):
                serialized_transcript['meeting_date'] = str(transcript['meeting_date'])
            serialized_transcripts.append(serialized_transcript)
        
        return jsonify({
            'success': True,
            'meeting': meeting,
            'transcripts': serialized_transcripts,
            'count': len(serialized_transcripts)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching transcripts: {str(e)}'
        }), 500

@app.route('/api/transcripts/<file_id>/content', methods=['GET'])
def get_transcript_content(file_id):
    """Get transcript content for display"""
    global drive_integration, is_authenticated
    
    if not is_authenticated or not drive_integration:
        return jsonify({
            'success': False,
            'message': 'Not authenticated'
        }), 401
    
    try:
        content = drive_integration.get_transcript_content(file_id)
        if content:
            return jsonify({
                'success': True,
                'content': content,
                'file_id': file_id
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Could not retrieve transcript content'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error retrieving transcript content: {str(e)}'
        }), 500

@app.route('/api/transcripts/<file_id>/download', methods=['GET'])
def download_transcript(file_id):
    """Download transcript file"""
    global drive_integration, is_authenticated
    
    if not is_authenticated or not drive_integration:
        return jsonify({
            'success': False,
            'message': 'Not authenticated'
        }), 401
    
    try:
        # Get file metadata first
        file_metadata = drive_integration.drive_service.files().get(fileId=file_id).execute()
        filename = file_metadata.get('name', 'transcript.docx')
        
        # Create a temporary filename for download
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_filename = f"temp_{timestamp}_{filename}"
        temp_path = f"transcripts/{temp_filename}"
        
        # Download the file
        downloaded_path = drive_integration.download_transcript(file_id, temp_path)
        
        if downloaded_path and os.path.exists(downloaded_path):
            return send_file(
                downloaded_path,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to download transcript'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error downloading transcript: {str(e)}'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    # Create transcripts directory
    os.makedirs('transcripts', exist_ok=True)
    
    # Start Flask app without initializing authentication
    print("Starting Google Meet Transcript API...")
    print("Authentication will be initialized when user clicks sign-in button.")
    
    # Run Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)
