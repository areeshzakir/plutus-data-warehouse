-- Create zoom_webinar_attendance table for cleaned webinar attendance data
CREATE TABLE IF NOT EXISTS public.zoom_webinar_attendance (
    id BIGSERIAL PRIMARY KEY,
    source_sheet TEXT NOT NULL,
    webinar_date DATE NOT NULL,
    category TEXT,
    attended TEXT,
    user_name TEXT,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    phone TEXT,
    registration_time TIMESTAMP WITH TIME ZONE,
    approval_status TEXT,
    join_time TIMESTAMP WITH TIME ZONE,
    leave_time TIMESTAMP WITH TIME ZONE,
    time_in_session_minutes INTEGER,
    is_guest TEXT,
    country_region_name TEXT,
    source TEXT,
    user_id TEXT,
    mon INTEGER,
    payload JSONB,
    ingested_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Unique constraint to prevent duplicates for the same person on the same webinar date
CREATE UNIQUE INDEX IF NOT EXISTS idx_zoom_webinar_unique
ON public.zoom_webinar_attendance (
    source_sheet,
    webinar_date,
    COALESCE(phone, ''),
    COALESCE(email, '')
);

CREATE INDEX IF NOT EXISTS idx_zoom_webinar_date ON public.zoom_webinar_attendance(webinar_date);
CREATE INDEX IF NOT EXISTS idx_zoom_webinar_phone ON public.zoom_webinar_attendance(phone);

ALTER TABLE public.zoom_webinar_attendance ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Enable all operations for service role" ON public.zoom_webinar_attendance;

CREATE POLICY "Enable all operations for service role"
    ON public.zoom_webinar_attendance
    FOR ALL
    USING (true)
    WITH CHECK (true);

GRANT ALL ON public.zoom_webinar_attendance TO postgres, anon, authenticated, service_role;
GRANT USAGE, SELECT ON SEQUENCE zoom_webinar_attendance_id_seq TO postgres, anon, authenticated, service_role;

COMMENT ON TABLE public.zoom_webinar_attendance IS 'Zoom webinar attendance cleaned and deduplicated by webinar date + phone/email';
COMMENT ON INDEX idx_zoom_webinar_unique IS 'Prevents duplicate rows for the same webinar_date + phone/email + source_sheet';
