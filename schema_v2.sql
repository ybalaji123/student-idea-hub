-- 1. DROP EXISTING CONFLICTING TABLES (OPTIONAL - RUN WITH CAUTION)
-- DROP TABLE IF EXISTS messages CASCADE;
-- DROP TABLE IF EXISTS requests CASCADE;
-- DROP TABLE IF EXISTS likes CASCADE;
-- DROP TABLE IF EXISTS comments CASCADE;
-- DROP TABLE IF EXISTS tasks CASCADE;
-- DROP TABLE IF EXISTS project_members CASCADE;
-- DROP TABLE IF EXISTS project_roles CASCADE;
-- DROP TABLE IF EXISTS events CASCADE;
-- DROP TABLE IF EXISTS ideas CASCADE;
-- DROP TABLE IF EXISTS projects CASCADE;
-- DROP TABLE IF EXISTS students CASCADE;
-- DROP TABLE IF EXISTS developers CASCADE;
-- DROP TABLE IF EXISTS users CASCADE;
-- DROP TABLE IF EXISTS chats CASCADE;
-- DROP TABLE IF EXISTS applications CASCADE;

-- 2. CREATE NEW TABLE SCHEMA (V2)

-- USERS (Unified Student/Developer/Mentor)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(50) DEFAULT 'Student', -- Student, Developer, Mentor
    skills JSONB DEFAULT '[]',
    bio TEXT,
    portfolio_links JSONB DEFAULT '[]',
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PROJECTS (Enhanced Ideas)
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    tags JSONB DEFAULT '[]', -- e.g. ["Python", "React"]
    domain VARCHAR(100), -- e.g. "Web Development"
    difficulty VARCHAR(50), -- e.g. "Beginner"
    required_roles JSONB DEFAULT '[]', -- e.g. ["Frontend", "Backend"]
    stage VARCHAR(50) DEFAULT 'Idea', -- Idea, Prototype, MVP
    repo_link VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    likes_count INTEGER DEFAULT 0
);

-- PROJECT MEMBERS (Collaboration)
CREATE TABLE IF NOT EXISTS project_members (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(100) NOT NULL, -- e.g. "Frontend Lead"
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, user_id)
);

-- TASKS (Kanban)
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    assigned_to INTEGER REFERENCES users(id) ON DELETE SET NULL,
    title VARCHAR(200) NOT NULL,
    status VARCHAR(50) DEFAULT 'To Do', -- To Do, In Progress, Done
    priority VARCHAR(50) DEFAULT 'Medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CHATS (Contextual Project Chat)
CREATE TABLE IF NOT EXISTS chats (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    sender_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- APPLICATIONS (Matchmaking)
CREATE TABLE IF NOT EXISTS applications (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    applicant_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role_applied_for VARCHAR(100),
    status VARCHAR(50) DEFAULT 'Pending', -- Pending, Accepted, Rejected
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
