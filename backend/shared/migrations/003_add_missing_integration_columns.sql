-- ============================================================================
-- NUCLEUS V1.2 - Migration 003: Add Missing Integration Columns
-- ============================================================================
-- Description: Adds missing columns to entity_integrations table
-- Author: NUCLEUS Development Team
-- Date: December 9, 2025
-- ============================================================================

-- Add missing columns to entity_integrations
ALTER TABLE dna.entity_integrations
ADD COLUMN IF NOT EXISTS last_sync_status VARCHAR(50),
ADD COLUMN IF NOT EXISTS sync_error_message TEXT,
ADD COLUMN IF NOT EXISTS next_sync_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS sync_settings JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS meta_data JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS created_by VARCHAR(255);

-- Update sync_frequency_hours column name if it exists (should be in sync_settings instead)
-- This is optional - keeping it for backward compatibility

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 003 completed successfully!';
    RAISE NOTICE '   - Added 6 missing columns to entity_integrations';
    RAISE NOTICE '   - last_sync_status, sync_error_message, next_sync_at';
    RAISE NOTICE '   - sync_settings, meta_data, created_by';
END $$;
