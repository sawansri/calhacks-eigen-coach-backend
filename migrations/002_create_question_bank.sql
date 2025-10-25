-- Migration script to create the questions table for the question bank

CREATE TABLE IF NOT EXISTS questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question_prompt TEXT NOT NULL,
    answer TEXT NOT NULL,
    explanation TEXT,
    difficulty VARCHAR(50) DEFAULT 'medium',
    topic_tag1 VARCHAR(255) NOT NULL,
    topic_tag2 VARCHAR(255),
    topic_tag3 VARCHAR(255),
    has_been_asked TINYINT(1) DEFAULT 0,
    source VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_question_prompt (question_prompt(255)),
    INDEX idx_topic_tag1 (topic_tag1),
    INDEX idx_topic_tag2 (topic_tag2),
    INDEX idx_topic_tag3 (topic_tag3)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
