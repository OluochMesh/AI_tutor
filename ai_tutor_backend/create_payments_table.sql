-- SQL script to create the payments table for M-Pesa integration
-- Create the payments table
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    checkout_request_id VARCHAR(100),
    merchant_request_id VARCHAR(100),
    mpesa_receipt_number VARCHAR(50),
    amount INTEGER NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    account_reference VARCHAR(100),
    transaction_desc VARCHAR(255),
    status VARCHAR(20),
    result_code VARCHAR(10),
    result_desc VARCHAR(255),
    plan_type VARCHAR(20),
    subscription_activated BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Foreign key constraint
    CONSTRAINT fk_payments_user_id 
        FOREIGN KEY (user_id) 
        REFERENCES users(id) 
        ON DELETE CASCADE
);

-- Create unique index on checkout_request_id
CREATE UNIQUE INDEX IF NOT EXISTS ix_payments_checkout_request_id 
    ON payments(checkout_request_id);

-- Create unique index on mpesa_receipt_number
CREATE UNIQUE INDEX IF NOT EXISTS ix_payments_mpesa_receipt_number 
    ON payments(mpesa_receipt_number);

-- Add comment to table
COMMENT ON TABLE payments IS 'M-Pesa payment transactions tracking table';

-- Add comments to key columns
COMMENT ON COLUMN payments.checkout_request_id IS 'M-Pesa STK Push checkout request ID';
COMMENT ON COLUMN payments.mpesa_receipt_number IS 'M-Pesa transaction receipt number';
COMMENT ON COLUMN payments.status IS 'Payment status: pending, completed, cancelled, failed, timeout';
COMMENT ON COLUMN payments.subscription_activated IS 'Whether subscription was activated after payment';

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update updated_at on row update
CREATE TRIGGER update_payments_updated_at
    BEFORE UPDATE ON payments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

