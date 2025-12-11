-- Migration 003: Add Success Metrics to Entity
-- Phase 1 - V2.0: Core Success Metrics
-- Date: 2025-12-10

-- Add success metrics columns to dna.entity table
ALTER TABLE dna.entity 
ADD COLUMN IF NOT EXISTS ttv_weeks FLOAT,
ADD COLUMN IF NOT EXISTS precision_at_3 FLOAT,
ADD COLUMN IF NOT EXISTS coherence_percent FLOAT;

-- Add comments for documentation
COMMENT ON COLUMN dna.entity.ttv_weeks IS 'Time To Value in weeks (30% to 50% autonomy)';
COMMENT ON COLUMN dna.entity.precision_at_3 IS 'Percentage of top-3 suggestions rated as highly relevant';
COMMENT ON COLUMN dna.entity.coherence_percent IS 'Percentage of actions aligned with DNA and principles';

-- Create index for metrics queries (optional but recommended)
CREATE INDEX IF NOT EXISTS idx_entity_metrics ON dna.entity(ttv_weeks, precision_at_3, coherence_percent);
