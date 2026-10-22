-- Private journal; never exposes responses over HTTP.
CREATE TABLE IF NOT EXISTS schnapper_runs (
 slot TEXT PRIMARY KEY,
 task_id TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('started','completed','blocked')),
 started_utc TEXT NOT NULL,
 ended_utc TEXT,
 error TEXT NOT NULL DEFAULT '',
 attempted_calls INTEGER NOT NULL DEFAULT 0 CHECK(attempted_calls >= 0 AND attempted_calls <= 4)
);
CREATE TABLE IF NOT EXISTS schnapper_reports (
 slot TEXT NOT NULL,
 role TEXT NOT NULL CHECK(role IN ('LEAD','BRAIN','CHECK','COMMAND')),
 model TEXT NOT NULL,
 content TEXT NOT NULL,
 sha256 TEXT NOT NULL CHECK(length(sha256) = 64),
 created_utc TEXT NOT NULL,
 PRIMARY KEY(slot,role),
 FOREIGN KEY(slot) REFERENCES schnapper_runs(slot)
);
CREATE INDEX IF NOT EXISTS schnapper_runs_recent ON schnapper_runs(started_utc DESC);
