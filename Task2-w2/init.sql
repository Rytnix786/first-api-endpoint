-- Setup schema for the visits counter database
CREATE TABLE IF NOT EXISTS visits (
    id SERIAL PRIMARY KEY,
    visited_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create index for visited_at column
CREATE INDEX IF NOT EXISTS idx_visits_visited_at ON visits (visited_at);
