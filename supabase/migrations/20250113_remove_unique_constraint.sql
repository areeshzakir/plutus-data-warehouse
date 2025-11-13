-- Update unique constraint to prevent EXACT duplicate records
-- A duplicate = ALL fields identical (name, email, phone, city, question, utm fields, date, ad, source)
-- This allows:
--   - Same user with different dates
--   - Same user with different campaigns
--   - Same user from different source sheets
-- But blocks exact duplicates even if script runs multiple times

-- Drop old constraints
ALTER TABLE public.tofu_leads 
DROP CONSTRAINT IF EXISTS tofu_leads_unique_record;

ALTER TABLE public.tofu_leads 
DROP CONSTRAINT IF EXISTS tofu_leads_user_id_key;

-- Create unique index on ALL fields that define a unique record
-- Using NULLS NOT DISTINCT to treat NULL values as equal
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
