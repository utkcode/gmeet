import React, { useState, useEffect } from 'react';
import './App.css';
import AuthButton from './components/AuthButton';
import MeetingList from './components/MeetingList';
import TranscriptViewer from './components/TranscriptViewer';

const API_BASE_URL = 'http://localhost:5000/api';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedMeeting, setSelectedMeeting] = useState(null);
  const [selectedTranscript, setSelectedTranscript] = useState(null);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/status`);
      const data = await response.json();
      setIsAuthenticated(data.authenticated);
    } catch (error) {
      console.error('Error checking auth status:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogin = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      const data = await response.json();
      
      if (data.success) {
        setIsAuthenticated(true);
      } else {
        alert('Login failed: ' + data.message);
      }
    } catch (error) {
      console.error('Login error:', error);
      alert('Login failed: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleMeetingSelect = (meeting) => {
    setSelectedMeeting(meeting);
    setSelectedTranscript(null);
  };

  const handleTranscriptSelect = (transcript) => {
    setSelectedTranscript(transcript);
  };

  const handleBackToMeetings = () => {
    setSelectedMeeting(null);
    setSelectedTranscript(null);
  };

  const handleBackToTranscripts = () => {
    setSelectedTranscript(null);
  };

  if (isLoading) {
    return (
      <div className="app">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Google Meet Transcript Viewer</h1>
        <p>Access and download your meeting transcripts</p>
      </header>

      <main className="app-main">
        {!isAuthenticated ? (
          <div className="auth-container">
            <div className="auth-card">
              <h2>Welcome!</h2>
              <p>Sign in with your Google account to access your meeting transcripts.</p>
              <AuthButton onLogin={handleLogin} isLoading={isLoading} />
            </div>
          </div>
        ) : !selectedMeeting ? (
          <MeetingList 
            onMeetingSelect={handleMeetingSelect}
            apiBaseUrl={API_BASE_URL}
          />
        ) : !selectedTranscript ? (
          <TranscriptViewer
            meeting={selectedMeeting}
            onTranscriptSelect={handleTranscriptSelect}
            onBack={handleBackToMeetings}
            apiBaseUrl={API_BASE_URL}
          />
        ) : (
          <div className="transcript-content">
            <div className="transcript-header">
              <button className="back-button" onClick={handleBackToTranscripts}>
                ← Back to Transcripts
              </button>
              <h2>{selectedTranscript.name}</h2>
            </div>
            <div className="transcript-text">
              <pre>{selectedTranscript.content}</pre>
            </div>
            <div className="transcript-actions">
              <button 
                className="download-button"
                onClick={() => {
                  const link = document.createElement('a');
                  link.href = `${API_BASE_URL}/transcripts/${selectedTranscript.file_id}/download`;
                  link.download = selectedTranscript.name;
                  document.body.appendChild(link);
                  link.click();
                  document.body.removeChild(link);
                }}
              >
                Download Transcript
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
