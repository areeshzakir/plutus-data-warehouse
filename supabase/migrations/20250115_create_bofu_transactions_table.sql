-- Create bofu_transactions table for transaction data
CREATE TABLE IF NOT EXISTS public.bofu_transactions (
    id BIGSERIAL PRIMARY KEY,
    txn_id TEXT NOT NULL UNIQUE,
    mongo_id TEXT,
    status TEXT,
    sid TEXT,
    emi_id TEXT,
    pid TEXT,
    payment_gateway TEXT,
    target TEXT,
    target_super_group TEXT,
    course_name TEXT,
    source TEXT,
    token_amount TEXT,
    without_token_paid_amount TEXT,
    created_on TEXT,
    p_type TEXT,
    ebook_rev TEXT,
    book_rev TEXT,
    payment_type TEXT,
    dp TEXT,
    total_emis TEXT,
    last_emi_date TEXT,
    total_emis_due TEXT,
    total_timely_emis_paid TEXT,
    paid_amount TEXT,
    core_partner TEXT,
    student_email TEXT,
    student_contact TEXT,
    student_signup_date TEXT,
    student_name TEXT,
    total_amount TEXT,
    product TEXT,
    mandate_status TEXT,
    ebook_net_amount TEXT,
    book_net_amount TEXT,
    product_net_amount TEXT,
    net_amount TEXT,
    employee_name TEXT,
    employee_team TEXT,
    total_emi TEXT,
    paid_emi_count TEXT,
    unpaid_emi_count TEXT,
    paid_emi_amount TEXT,
    unpaid_amount TEXT,
    last_paid_date TEXT,
    net_amount_after_pdd TEXT,
    payload JSONB,
    ingested_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_bofu_transactions_txn_id ON public.bofu_transactions(txn_id);
CREATE INDEX IF NOT EXISTS idx_bofu_transactions_created_on ON public.bofu_transactions(created_on);

ALTER TABLE public.bofu_transactions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Enable all operations for service role" ON public.bofu_transactions;

CREATE POLICY "Enable all operations for service role"
    ON public.bofu_transactions
    FOR ALL
    USING (true)
    WITH CHECK (true);

GRANT ALL ON public.bofu_transactions TO postgres, anon, authenticated, service_role;
GRANT USAGE, SELECT ON SEQUENCE bofu_transactions_id_seq TO postgres, anon, authenticated, service_role;

COMMENT ON TABLE public.bofu_transactions IS 'Bottom-of-funnel transactions fetched from Testbook API';
