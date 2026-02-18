import psycopg2
import os

# Use the URL from database.py
DATABASE_URL = "postgresql://postgres.ddqnipwmeueypbkvaxoo:Yemineni%40123@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

def init_db():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("Connected to database...")

        # --- DROP OLD TABLES (Clean Slate) ---
        # Dropping in order of dependencies
        tables_to_drop = [
            "direct_messages", "applications", "chats", # New tables
            "messages", "requests", "likes", "comments", # Interaction tables
            "tasks", "project_members", "project_roles", "events", # New tables (if any existed)
            "ideas", "projects", # Core content
            "students", "developers", "users" # Auth
        ]
        
        for table in tables_to_drop:
            cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
            print(f"Dropped table: {table}")

        # --- CREATE NEW TABLE SCHEMA (V2) ---

        # 1. USERS (Unified)
        cur.execute("""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                role VARCHAR(50) DEFAULT 'Student', -- Student, Developer, Mentor
                skills JSONB DEFAULT '[]',
                bio TEXT,
                portfolio_links JSONB DEFAULT '[]',
                avatar_url TEXT,
                phone_number VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("Created table: users")

        # 2. PROJECTS (Enhanced Ideas)
        cur.execute("""
            CREATE TABLE projects (
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
        """)
        print("Created table: projects")

        # 3. PROJECT MEMBERS (Collaboration)
        cur.execute("""
            CREATE TABLE project_members (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                role VARCHAR(100) NOT NULL, -- e.g. "Frontend Lead"
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(project_id, user_id)
            );
        """)
        print("Created table: project_members")

        # 4. TASKS (Kanban)
        cur.execute("""
            CREATE TABLE tasks (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                assigned_to INTEGER REFERENCES users(id) ON DELETE SET NULL,
                title VARCHAR(200) NOT NULL,
                status VARCHAR(50) DEFAULT 'To Do', -- To Do, In Progress, Done
                priority VARCHAR(50) DEFAULT 'Medium',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("Created table: tasks")

        # 5. MESSAGES/CHATS (Contextual)
        cur.execute("""
            CREATE TABLE chats (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                sender_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("Created table: chats")

        # 6. APPLICATIONS/REQUESTS (Matchmaking)
        cur.execute("""
            CREATE TABLE applications (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                applicant_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                role_applied_for VARCHAR(100),
                status VARCHAR(50) DEFAULT 'Pending', -- Pending, Accepted, Rejected
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("Created table: applications")

        # 7. DIRECT MESSAGES
        cur.execute("""
            CREATE TABLE direct_messages (
                id SERIAL PRIMARY KEY,
                sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                receiver_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                message TEXT NOT NULL,
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            CREATE INDEX idx_dm_sender_receiver ON direct_messages(sender_id, receiver_id);
        """)
        print("Created table: direct_messages")

        # 8. EVENTS
        cur.execute("""
            CREATE TABLE events (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                date TIMESTAMP NOT NULL,
                location VARCHAR(100), -- "Online" or physical address
                organizer_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                tags JSONB DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("Created table: events")

        # 9. NOTIFICATIONS
        cur.execute("""
            CREATE TABLE notifications (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                type VARCHAR(50) NOT NULL, -- "Message", "Application", "System"
                title VARCHAR(100) NOT NULL,
                message TEXT,
                link VARCHAR(255), -- Action URL
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("Created table: notifications")

        conn.commit()
        print("Schema successfully initialized!")
        
        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    init_db()
