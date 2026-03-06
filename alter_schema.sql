-- ============================================
-- OLMS — PostgreSQL Database Migration
-- ============================================

-- -------------------------------------------
-- Notifications table (Feature 2)
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    notif_type VARCHAR(20) DEFAULT 'info',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------
-- Messages table (Feature 3 – Chat)
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    sender_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    receiver_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------
-- Fines table (Feature 5)
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS fines (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    issued_book_id INT NOT NULL REFERENCES issued_books(id) ON DELETE CASCADE,
    amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    is_paid BOOLEAN NOT NULL DEFAULT FALSE,
    paid_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, issued_book_id)
);

-- -------------------------------------------
-- Add columns
-- -------------------------------------------
ALTER TABLE books ADD COLUMN IF NOT EXISTS borrow_count INT NOT NULL DEFAULT 0;
ALTER TABLE books ADD COLUMN IF NOT EXISTS qr_code TEXT NULL;
