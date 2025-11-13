-- ============================================================================
-- MIGRATION: Update unique constraint for exact duplicate detection
-- ============================================================================
-- Run this in Supabase SQL Editor: 
-- https://supabase.com/dashboard/project/rwrfabtpzyzjbfwyogcm/editor
-- ============================================================================

-- Step 1: Drop old constraints
ALTER TABLE public.tofu_leads 
DROP CONSTRAINT IF EXISTS tofu_leads_unique_record;

ALTER TABLE public.tofu_leads 
DROP CONSTRAINT IF EXISTS tofu_leads_user_id_key;

-- Step 2: Create unique index on ALL fields that define a unique record
-- This treats NULL values as equal using COALESCE
CREATE UNIQUE INDEX IF NOT EXISTS idx_tofu_leads_all_fields_unique 
ON public.tofu_leads(
    COALESCE(name, ''),
    COALESCE(email, ''),
    COALESCE(phone_number, ''),
    COALESCE(city, ''),
    COALESCE(question_1, ''),
    COALESCE(utm_source, ''),
    COALESCE(utm_medium, ''),
    COALESCE(utm_camp, ''),
    created_date,
    COALESCE(ad_name, ''),
    COALESCE(source_sheet, '')
);

COMMENT ON INDEX idx_tofu_leads_all_fields_unique IS 'Prevents exact duplicate records - all fields must match to be considered duplicate';

-- Step 3: Verify the index was created
SELECT 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE tablename = 'tofu_leads' 
AND indexname = 'idx_tofu_leads_all_fields_unique';
