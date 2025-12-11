-- Migration: Add master_prompt fields to Entity table
-- Date: 2025-12-11
-- Purpose: Enable Master Prompt layer for DNA-to-Agent flow

-- Add master_prompt field
ALTER TABLE dna.entity
ADD COLUMN IF NOT EXISTS master_prompt TEXT;

-- Add master_prompt_version field
ALTER TABLE dna.entity
ADD COLUMN IF NOT EXISTS master_prompt_version INTEGER DEFAULT 1;

-- Add master_prompt_updated_at field
ALTER TABLE dna.entity
ADD COLUMN IF NOT EXISTS master_prompt_updated_at TIMESTAMP WITH TIME ZONE;

-- Add comments
COMMENT ON COLUMN dna.entity.master_prompt IS 'Core identity prompt generated from complete DNA profile';
COMMENT ON COLUMN dna.entity.master_prompt_version IS 'Version number of master prompt';
COMMENT ON COLUMN dna.entity.master_prompt_updated_at IS 'When master prompt was last updated';

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_entity_master_prompt_updated 
ON dna.entity(master_prompt_updated_at DESC);
