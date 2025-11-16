-- Create mofu_lead_assignments table for lead assignment data
CREATE TABLE IF NOT EXISTS public.mofu_lead_assignments (
    id BIGSERIAL PRIMARY KEY,
    sources TEXT NOT NULL,
    assign_on TIMESTAMP WITH TIME ZONE NOT NULL,
    lead_mobile TEXT NOT NULL,
    employee TEXT,
    payload JSONB,
    ingested_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Unique constraint to prevent exact duplicates for the same source + timestamp + lead
ALTER TABLE public.mofu_lead_assignments 
ADD CONSTRAINT mofu_unique_assignment UNIQUE (sources, assign_on, lead_mobile);

CREATE INDEX IF NOT EXISTS idx_mofu_assign_on ON public.mofu_lead_assignments(assign_on);
CREATE INDEX IF NOT EXISTS idx_mofu_sources ON public.mofu_lead_assignments(sources);

ALTER TABLE public.mofu_lead_assignments ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Enable all operations for service role" ON public.mofu_lead_assignments;

CREATE POLICY "Enable all operations for service role"
    ON public.mofu_lead_assignments
    FOR ALL
    USING (true)
    WITH CHECK (true);

GRANT ALL ON public.mofu_lead_assignments TO postgres, anon, authenticated, service_role;
GRANT USAGE, SELECT ON SEQUENCE mofu_lead_assignments_id_seq TO postgres, anon, authenticated, service_role;

COMMENT ON TABLE public.mofu_lead_assignments IS 'Middle-of-funnel lead assignments fetched from MOFU API';
COMMENT ON CONSTRAINT mofu_unique_assignment ON public.mofu_lead_assignments IS 'Prevents duplicate lead assignments for the same source + timestamp + lead mobile';
