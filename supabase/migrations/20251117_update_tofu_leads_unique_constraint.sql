-- Loosen tofu_leads uniqueness: allow reruns to insert minor variations
-- Old index: idx_tofu_leads_all_fields_unique on all fields (blocked exact duplicates across reruns)

DO $$
BEGIN
    -- Drop the existing unique index (if present)
    PERFORM 1 FROM pg_indexes WHERE schemaname = 'public' AND indexname = 'idx_tofu_leads_all_fields_unique';
    IF FOUND THEN
        EXECUTE 'DROP INDEX IF EXISTS idx_tofu_leads_all_fields_unique';
    END IF;

    -- Safely delete duplicate rows for the new key, keeping the smallest id
    WITH dupes AS (
        SELECT id,
               ROW_NUMBER() OVER (
                   PARTITION BY COALESCE(user_id, ''), created_date, COALESCE(source_sheet, '')
                   ORDER BY id ASC
               ) AS rn
        FROM public.tofu_leads
    )
    DELETE FROM public.tofu_leads t
    USING dupes d
    WHERE t.id = d.id
      AND d.rn > 1;

    -- Create the new unique index
    PERFORM 1 FROM pg_indexes WHERE schemaname = 'public' AND indexname = 'idx_tofu_leads_identity_unique';
    IF NOT FOUND THEN
        EXECUTE 'CREATE UNIQUE INDEX idx_tofu_leads_identity_unique ON public.tofu_leads (COALESCE(user_id, ''''''), created_date, COALESCE(source_sheet, ''''''))';
        EXECUTE 'COMMENT ON INDEX idx_tofu_leads_identity_unique IS ''Prevents duplicate users per created_date per sheet; allows reruns to insert variants''';
    END IF;
END $$;
