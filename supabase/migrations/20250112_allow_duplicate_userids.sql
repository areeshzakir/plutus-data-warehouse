-- Allow multiple records per user_id while preventing exact duplicates
-- This enables tracking same user across different campaigns/dates

-- Drop the existing unique constraint on user_id
ALTER TABLE public.tofu_leads DROP CONSTRAINT IF EXISTS tofu_leads_user_id_key;

-- Create a composite unique constraint on key fields to prevent exact duplicates
-- This allows same user_id but prevents duplicate (user_id + campaign + date + source)
ALTER TABLE public.tofu_leads 
ADD CONSTRAINT tofu_leads_unique_record 
UNIQUE (user_id, created_date, utm_source, utm_medium, utm_camp, source_sheet);

-- Add comment explaining the constraint
COMMENT ON CONSTRAINT tofu_leads_unique_record ON public.tofu_leads IS 
'Prevents exact duplicate records while allowing same user from different campaigns/times';
