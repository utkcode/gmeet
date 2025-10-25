import React, { useState, useEffect } from 'react';
import './TranscriptViewer.css';

function TranscriptViewer({ meeting, onTranscriptSelect, onBack, apiBaseUrl }) {
  const [transcripts, setTranscripts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchTranscripts();
  }, [meeting.id]);

  const fetchTranscripts = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`${apiBaseUrl}/meetings/${meeting.id}/transcripts`);
      const data = await response.json();
      
      if (data.success) {
        setTranscripts(data.transcripts);
      } else {
        setError(data.message);
      }
    } catch (error) {
      console.error('Error fetching transcripts:', error);
      setError('Failed to fetch transcripts');
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return 'Unknown size';
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(1)} MB`;
  };

  const handleTranscriptClick = async (transcript) => {
    try {
      const response = await fetch(`${apiBaseUrl}/transcripts/${transcript.file_id}/content`);
      const data = await response.json();
      
      if (data.success) {
        onTranscriptSelect({
          ...transcript,
          content: data.content
        });
      } else {
        alert('Failed to load transcript content: ' + data.message);
      }
    } catch (error) {
      console.error('Error loading transcript content:', error);
      alert('Failed to load transcript content');
    }
  };

  if (isLoading) {
    return (
      <div className="transcript-viewer">
        <div className="transcript-header">
          <button className="back-button" onClick={onBack}>
            ← Back to Meetings
          </button>
          <h2>{meeting.title}</h2>
        </div>
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading transcripts...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="transcript-viewer">
        <div className="transcript-header">
          <button className="back-button" onClick={onBack}>
            ← Back to Meetings
          </button>
          <h2>{meeting.title}</h2>
        </div>
        <div className="error-container">
          <h3>Error</h3>
          <p>{error}</p>
          <button className="retry-button" onClick={fetchTranscripts}>
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (transcripts.length === 0) {
    return (
      <div className="transcript-viewer">
        <div className="transcript-header">
          <button className="back-button" onClick={onBack}>
            ← Back to Meetings
          </button>
          <h2>{meeting.title}</h2>
        </div>
        <div className="empty-container">
          <h3>No Transcripts Found</h3>
          <p>No transcripts were found for this meeting. Make sure the meeting was recorded and transcripts are available in your Google Drive.</p>
          <button className="retry-button" onClick={fetchTranscripts}>
            Refresh
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="transcript-viewer">
      <div className="transcript-header">
        <button className="back-button" onClick={onBack}>
          ← Back to Meetings
        </button>
        <h2>{meeting.title}</h2>
        <p className="meeting-date">{formatDate(meeting.start_time)}</p>
      </div>
      
      <div className="transcript-list">
        <h3>Available Transcripts</h3>
        <p>Click on a transcript to view its content</p>
        
        <div className="transcripts-grid">
          {transcripts.map((transcript) => (
            <div 
              key={transcript.file_id} 
              className="transcript-card"
              onClick={() => handleTranscriptClick(transcript)}
            >
              <div className="transcript-card-header">
                <h4>{transcript.name}</h4>
                <div className="transcript-meta">
                  <span className="file-size">{formatFileSize(transcript.size)}</span>
                  <span className="file-type">📄</span>
                </div>
              </div>
              
              <div className="transcript-card-content">
                {transcript.meeting_title && (
                  <p className="meeting-title">
                    <strong>Meeting:</strong> {transcript.meeting_title}
                  </p>
                )}
                
                {transcript.meeting_date && (
                  <p className="meeting-date">
                    <strong>Date:</strong> {transcript.meeting_date}
                  </p>
                )}
                
                <div className="transcript-details">
                  <div className="modified-time">
                    <span className="time-icon">🕒</span>
                    Modified: {formatDate(transcript.modified_time)}
                  </div>
                </div>
              </div>
              
              <div className="transcript-card-footer">
                <button className="view-transcript-button">
                  View Transcript →
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default TranscriptViewer;