-- ============================================================================
-- NUCLEUS V1.2 - Migration 004: Fix Scopes Column Type
-- ============================================================================
-- Description: Changes scopes column from TEXT[] to JSONB
-- Author: NUCLEUS Development Team
-- Date: December 9, 2025
-- ============================================================================

-- Change scopes column type from TEXT[] to JSONB
ALTER TABLE dna.entity_integrations
ALTER COLUMN scopes TYPE JSONB USING scopes::TEXT::JSONB;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 004 completed successfully!';
    RAISE NOTICE '   - Changed scopes column from TEXT[] to JSONB';
END $$;
