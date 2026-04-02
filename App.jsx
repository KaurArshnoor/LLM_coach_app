import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

const API = 'http://localhost:8000';

export default function App() {
  const [query, setQuery] = useState('');
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState('search');
  const [listening, setListening] = useState(false);

  const handleVoice = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Speech recognition is not supported in this browser. Use Chrome or Edge.');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => setListening(true);
    recognition.onend = () => setListening(false);

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setQuery(transcript);
      // Optional: immediately submit after voice capture
      handleSearch({ preventDefault: () => {} }, transcript);
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error', event.error);
      alert('Speech recognition error: ' + event.error);
      setListening(false);
    };

    recognition.start();
  };

  const handleSearch = async (e, overrideQuery) => {
    if (e && e.preventDefault) {
      e.preventDefault();
    }

    const effectiveQuery = overrideQuery !== undefined ? overrideQuery : query;
    if (!effectiveQuery || !effectiveQuery.trim()) {
      alert('Please enter a query.');
      return;
    }

    setLoading(true);
    try {
      const res = await axios.post(`${API}/recommend`, { query: effectiveQuery, top_k: 5 });
      setRecommendations(res.data.recommendations);
      setPage('results');
    } catch (err) {
      alert('Error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <header>
        <h1>🏋️ Coaching App</h1>
        <p>AI-powered exercise recommendations</p>
      </header>

      {page === 'search' && (
        <div className="page">
          <form onSubmit={handleSearch}>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Describe your fitness needs..."
              rows="4"
              disabled={loading}
            />
            <div className="button-row">
              <button type="button" onClick={handleVoice} disabled={loading}>
                {listening ? 'Listening...' : '🎙️ Speak'}
              </button>
              <button type="submit" disabled={loading || !query.trim()}>
                {loading ? 'Searching...' : 'Get Recommendations'}
              </button>
            </div>
          </form>
        </div>
      )}

      {page === 'results' && (
        <div className="page">
          <button onClick={() => setPage('search')} className="back">← Back</button>
          <h2>Results for: "{query}"</h2>
          {recommendations.length === 0 ? (
            <p>No recommendations found</p>
          ) : (
            <div className="recommendations">
              {recommendations.map((rec) => (
                <div key={rec.id} className="card">
                  <h3>#{rec.rank} {rec.title}</h3>
                  <p className="score">{(rec.score * 100).toFixed(0)}% Match</p>
                  <p><strong>Why:</strong> {rec.reasoning}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
