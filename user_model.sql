-- Bảng người dùng (student hoặc expert)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
);

-- Bảng bài đăng câu hỏi
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    content TEXT,
    questioner_id INTEGER,
    tag TEXT DEFAULT 'unanswered', -- trạng thái câu hỏi
    created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (questioner_id) REFERENCES users(id)
);

-- Bảng câu trả lời
CREATE TABLE IF NOT EXISTS answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT,
    answerer_id INTEGER,
    post_id INTEGER,
    created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (answerer_id) REFERENCES users(id),
    FOREIGN KEY (post_id) REFERENCES posts(id)
);