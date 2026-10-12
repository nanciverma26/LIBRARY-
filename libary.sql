CREATE DATABASE IF NOT EXISTS library_management;

USE library_management;

-- =========================
-- USERS TABLE
-- =========================

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('student', 'librarian') DEFAULT 'student',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =========================
-- BOOKS TABLE
-- =========================

CREATE TABLE IF NOT EXISTS books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    author VARCHAR(150) NOT NULL,
    category VARCHAR(100),
    isbn VARCHAR(50),
    total_copies INT NOT NULL DEFAULT 1,
    available_copies INT NOT NULL DEFAULT 1
);


-- =========================
-- ISSUES TABLE
-- =========================

CREATE TABLE IF NOT EXISTS issues (
    id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL,
    book_id INT NOT NULL,

    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    return_date DATE NULL,

    fine DECIMAL(10,2) DEFAULT 0,

    status ENUM('issued', 'returned') DEFAULT 'issued',

    FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (book_id) REFERENCES books(id)
        ON DELETE CASCADE
);


-- =========================
-- WAITING QUEUE TABLE
-- =========================

CREATE TABLE IF NOT EXISTS waiting_queue (
    id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL,
    book_id INT NOT NULL,

    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    status ENUM('waiting', 'completed') DEFAULT 'waiting',

    FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (book_id) REFERENCES books(id)
        ON DELETE CASCADE
);


-- =========================
-- SAMPLE BOOKS
-- =========================

INSERT INTO books
(title, author, category, isbn, total_copies, available_copies)
VALUES
('Python Programming', 'Eric Matthes', 'Programming', '9781593279288', 3, 3),

('Data Structures and Algorithms', 'Narasimha Karumanchi', 'Computer Science', '9788193245279', 2, 2),

('Database Management System', 'Raghu Ramakrishnan', 'Database', '9780072465631', 2, 2),

('Computer Networks', 'Andrew S. Tanenbaum', 'Networking', '9780132126953', 2, 2),

('Operating System Concepts', 'Abraham Silberschatz', 'Operating System', '9781118063330', 1, 1);