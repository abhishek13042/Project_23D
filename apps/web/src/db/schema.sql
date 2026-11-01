-- SPEC 011: run once in the Neon SQL editor. Keep in step with schema.ts.

CREATE TABLE IF NOT EXISTS inference_run (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz NOT NULL DEFAULT now(),
  status text NOT NULL CHECK (status IN ('success', 'failed')),
  duration_seconds real NOT NULL,
  voxel_count bigint,
  kidney_ml real,
  tumor_ml real,
  cyst_ml real,
  app_version text NOT NULL
);

CREATE TABLE IF NOT EXISTS feedback (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz NOT NULL DEFAULT now(),
  run_id uuid REFERENCES inference_run (id) ON DELETE SET NULL,
  rating smallint NOT NULL CHECK (rating BETWEEN 1 AND 5),
  comment text CHECK (char_length(comment) <= 1000)
);
