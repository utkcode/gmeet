import React, { useState, useEffect } from 'react';
import './MeetingList.css';

function MeetingList({ onMeetingSelect, apiBaseUrl }) {
  const [meetings, setMeetings] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchMeetings();
  }, []);

  const fetchMeetings = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`${apiBaseUrl}/meetings`);
      const data = await response.json();
      
      if (data.success) {
        setMeetings(data.meetings);
      } else {
        setError(data.message);
      }
    } catch (error) {
      console.error('Error fetching meetings:', error);
      setError('Failed to fetch meetings');
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

  if (isLoading) {
    return (
      <div className="meeting-list">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading meetings...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="meeting-list">
        <div className="error-container">
          <h3>Error</h3>
          <p>{error}</p>
          <button className="retry-button" onClick={fetchMeetings}>
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (meetings.length === 0) {
    return (
      <div className="meeting-list">
        <div className="empty-container">
          <h3>No Meetings Found</h3>
          <p>No Google Meet meetings found in your calendar for the past 3 months.</p>
          <button className="retry-button" onClick={fetchMeetings}>
            Refresh
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="meeting-list">
      <div className="meeting-list-header">
        <h2>Your Google Meet Meetings</h2>
        <p>Select a meeting to view available transcripts</p>
        <button className="refresh-button" onClick={fetchMeetings}>
          Refresh
        </button>
      </div>
      
      <div className="meetings-grid">
        {meetings.map((meeting) => (
          <div 
            key={meeting.id} 
            className="meeting-card"
            onClick={() => onMeetingSelect(meeting)}
          >
            <div className="meeting-card-header">
              <h3>{meeting.title}</h3>
              <div className="meeting-date">
                {formatDate(meeting.start_time)}
              </div>
            </div>
            
            <div className="meeting-card-content">
              {meeting.description && (
                <p className="meeting-description">
                  {meeting.description.length > 100 
                    ? `${meeting.description.substring(0, 100)}...` 
                    : meeting.description
                  }
                </p>
              )}
              
              <div className="meeting-details">
                {meeting.attendees && meeting.attendees.length > 0 && (
                  <div className="attendees-count">
                    <span className="attendees-icon">👥</span>
                    {meeting.attendees.length} attendee{meeting.attendees.length !== 1 ? 's' : ''}
                  </div>
                )}
                
                <div className="meeting-link">
                  <span className="link-icon">🔗</span>
                  Google Meet
                </div>
              </div>
            </div>
            
            <div className="meeting-card-footer">
              <button className="select-meeting-button">
                View Transcripts →
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default MeetingList;