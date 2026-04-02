-- Coaching App Database Schema (Minimal)
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE exercises (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    tags TEXT,
    body_part VARCHAR(100),
    difficulty VARCHAR(50),
    equipment VARCHAR(255),
    injury_focus VARCHAR(255),
    intensity VARCHAR(50)
);

CREATE TABLE query_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100),
    query TEXT NOT NULL,
    retrieved_ids TEXT,
    ranked_ids TEXT,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_profiles (
    user_id VARCHAR(100) PRIMARY KEY,
    goals TEXT,
    constraints TEXT,
    preferences TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_exercises_body_part ON exercises(body_part);
CREATE INDEX idx_exercises_difficulty ON exercises(difficulty);
CREATE INDEX idx_exercises_tags ON exercises USING GIN(to_tsvector('english', tags));
CREATE INDEX idx_query_logs_user ON query_logs(user_id);
