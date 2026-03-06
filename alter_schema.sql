-- ============================================
-- OLMS — Database Migration for New Features
-- Run after the initial schema.sql
-- ============================================

USE olms_db;

-- -------------------------------------------
-- Notifications table (Feature 2)
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    is_read TINYINT(1) NOT NULL DEFAULT 0,
    notif_type ENUM('info', 'warning', 'success', 'danger') DEFAULT 'info',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- -------------------------------------------
-- Messages table (Feature 3 – Chat)
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    message TEXT NOT NULL,
    is_read TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
);

-- -------------------------------------------
-- Fines table (Feature 5)
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS fines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    issued_book_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    is_paid TINYINT(1) NOT NULL DEFAULT 0,
    paid_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (issued_book_id) REFERENCES issued_books(id) ON DELETE CASCADE
);

-- -------------------------------------------
-- Add borrow_count to books (Feature 7)
-- -------------------------------------------
ALTER TABLE books ADD COLUMN borrow_count INT NOT NULL DEFAULT 0;

-- -------------------------------------------
-- Add qr_code to books (Feature 6)
-- -------------------------------------------
ALTER TABLE books ADD COLUMN qr_code LONGTEXT NULL;
