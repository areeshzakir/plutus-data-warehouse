-- Create tofu_leads table for storing marketing funnel top-of-funnel data
CREATE TABLE IF NOT EXISTS public.tofu_leads (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    name TEXT,
    email TEXT,
    phone_number TEXT,
    city TEXT,
    question_1 TEXT,
    utm_source TEXT,
    utm_medium TEXT,
    utm_camp TEXT,
    created_date TIMESTAMP,
    ad_name TEXT,
    source_sheet TEXT,
    ingested_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Create index on user_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_tofu_leads_user_id ON public.tofu_leads(user_id);

-- Create index on created_date for incremental loading
CREATE INDEX IF NOT EXISTS idx_tofu_leads_created_date ON public.tofu_leads(created_date);

-- Create index on source_sheet for filtering
CREATE INDEX IF NOT EXISTS idx_tofu_leads_source_sheet ON public.tofu_leads(source_sheet);

-- Add updated_at trigger
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_tofu_leads_updated_at
    BEFORE UPDATE ON public.tofu_leads
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE public.tofu_leads ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations for service role
CREATE POLICY "Enable all operations for service role"
    ON public.tofu_leads
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Grant permissions
GRANT ALL ON public.tofu_leads TO postgres, anon, authenticated, service_role;
GRANT USAGE, SELECT ON SEQUENCE tofu_leads_id_seq TO postgres, anon, authenticated, service_role;

-- Add comment to table
COMMENT ON TABLE public.tofu_leads IS 'Top of funnel leads from Google Sheets marketing campaigns';
