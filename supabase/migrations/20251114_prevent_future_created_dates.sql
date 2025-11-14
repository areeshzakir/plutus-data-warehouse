-- Prevent future-dated created_date values from entering tofu_leads
-- Allows NULL created_date but blocks anything more than 1 day ahead of current UTC time

ALTER TABLE public.tofu_leads
DROP CONSTRAINT IF EXISTS tofu_leads_created_date_future_check;

ALTER TABLE public.tofu_leads
ADD CONSTRAINT tofu_leads_created_date_future_check
CHECK (
    created_date IS NULL
    OR created_date <= (NOW() AT TIME ZONE 'UTC') + INTERVAL '1 day'
);

COMMENT ON CONSTRAINT tofu_leads_created_date_future_check ON public.tofu_leads
IS 'Reject rows whose created_date is set more than 1 day in the future (UTC).';
