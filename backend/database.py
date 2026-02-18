from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from passlib.context import CryptContext
from typing import List, Optional, Any
from datetime import datetime

import os

# --- CONFIG ---
# Use environment variable for production, fallback to local string for development
# CRITICAL: In Render, add an Environment Variable named 'DATABASE_URL' with your connection string.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres.ddqnipwmeueypbkvaxoo:Yemineni%40123@aws-1-ap-south-1.pooler.supabase.com:6543/postgres")

app = FastAPI(title="Student Idea Hub V2 API")

# --- SECURITY ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# --- DB HELPER ---
def get_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "https://ybalaji123.github.io"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELS ---
# --- MODELS ---
class UserSignup(BaseModel):
    full_name: str
    email: str
    password: str
    role: str = "Student" # Student, Developer, Mentor
    skills: List[str] = []
    bio: Optional[str] = None
    portfolio_links: List[str] = []
    avatar_url: Optional[str] = None
    phone_number: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class ProjectCreate(BaseModel):
    owner_id: int
    title: str
    description: str
    tags: List[str] = []
    domain: str
    difficulty: str
    required_roles: List[str] = []
    stage: str = "Idea"
    repo_link: Optional[str] = None

class TaskCreate(BaseModel):
    project_id: int
    assigned_to: Optional[int]
    title: str
    status: str = "To Do"
    priority: str = "Medium"

class ApplicationCreate(BaseModel):
    project_id: int
    applicant_id: int
    role_applied_for: str
    message: str

class ChatMessageCreate(BaseModel):
    project_id: int
    sender_id: int
    message: str

# --- AUTH ROUTES ---

@app.post("/auth/signup")
def signup(user: UserSignup):
    conn = get_connection()
    cur = conn.cursor()
    try:
        hashed_pw = hash_password(user.password)
        # Store skills/portfolio as JSONB
        import json
        skills_json = json.dumps(user.skills)
        portfolio_json = json.dumps(user.portfolio_links)
        
        cur.execute("""
            INSERT INTO users (full_name, email, password_hash, role, skills, bio, portfolio_links, avatar_url, phone_number)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id, full_name, role
        """, (user.full_name, user.email, hashed_pw, user.role, skills_json, user.bio, portfolio_json, user.avatar_url, user.phone_number))
        
        new_user = cur.fetchone()
        conn.commit()
        return {"message": "User registered", "user": new_user}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close(); conn.close()

@app.post("/auth/login")
def login(creds: UserLogin):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email=%s", (creds.email,))
    user = cur.fetchone()
    cur.close(); conn.close()

    if not user or not verify_password(creds.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {
        "user": {
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "role": user["role"],
            "skills": user["skills"],
            "bio": user["bio"],
            "portfolio_links": user["portfolio_links"],
            "avatar_url": user["avatar_url"],
            "phone_number": user["phone_number"]
        }
    }

@app.get("/users")
def get_users(role: Optional[str] = None, skill: Optional[str] = None):
    conn = get_connection(); cur = conn.cursor()
    query = """
        SELECT id, full_name, email, role, skills, bio, portfolio_links, avatar_url, phone_number, created_at
        FROM users
    """
    params = []
    conditions = []
    
    if role and role != "All":
        conditions.append("role = %s")
        params.append(role)
        
    if skill:
        conditions.append("skills @> %s")
        import json
        params.append(json.dumps([skill]))
        
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
        
    query += " ORDER BY created_at DESC"
    
    cur.execute(query, tuple(params))
    users = cur.fetchall()
    conn.close()
    return users

# --- PROJECT ROUTES ---

@app.get("/projects")
def get_projects(tag: Optional[str] = None, mine: Optional[bool] = False, user_id: Optional[int] = None):
    conn = get_connection(); cur = conn.cursor()
    
    query = """
        SELECT p.*, u.full_name as owner_name, u.avatar_url as owner_avatar
        FROM projects p
        JOIN users u ON p.owner_id = u.id
    """
    params = []
    
    if mine and user_id:
        query += " WHERE p.owner_id = %s"
        params.append(user_id)
    elif tag:
        # JSONB contains check
        query += " WHERE p.tags @> %s"
        import json
        params.append(json.dumps([tag]))
        
    query += " ORDER BY p.created_at DESC"
    
    cur.execute(query, tuple(params))
    projects = cur.fetchall()
    conn.close()
    return projects

@app.get("/projects/{project_id}")
def get_project_detail(project_id: int):
    conn = get_connection(); cur = conn.cursor()
    
    # Get Project Info
    cur.execute("""
        SELECT p.*, u.full_name as owner_name 
        FROM projects p 
        JOIN users u ON p.owner_id = u.id 
        WHERE p.id = %s
    """, (project_id,))
    project = cur.fetchone()
    
    if not project:
        conn.close()
        raise HTTPException(status_code=404, detail="Project not found")
        
    # Get Members
    cur.execute("""
        SELECT pm.*, u.full_name 
        FROM project_members pm
        JOIN users u ON pm.user_id = u.id
        WHERE pm.project_id = %s
    """, (project_id,))
    members = cur.fetchall()
    
    # Get Tasks (Kanban)
    cur.execute("SELECT * FROM tasks WHERE project_id = %s", (project_id,))
    tasks = cur.fetchall()
    
    conn.close()
    return {"project": project, "members": members, "tasks": tasks}

@app.post("/projects")
def create_project(p: ProjectCreate):
    conn = get_connection(); cur = conn.cursor()
    import json
    try:
        cur.execute("""
            INSERT INTO projects (owner_id, title, description, tags, domain, difficulty, required_roles, stage, repo_link)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (p.owner_id, p.title, p.description, json.dumps(p.tags), p.domain, p.difficulty, json.dumps(p.required_roles), p.stage, p.repo_link))
        pid = cur.fetchone()['id']
        conn.commit()
        return {"message": "Project created", "id": pid}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
@app.put("/projects/{project_id}")
def update_project(project_id: int, p: ProjectCreate):
    conn = get_connection(); cur = conn.cursor()
    import json
    try:
        # Verify ownership
        cur.execute("SELECT owner_id FROM projects WHERE id = %s", (project_id,))
        proj = cur.fetchone()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found")
        if proj['owner_id'] != p.owner_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        cur.execute("""
            UPDATE projects 
            SET title = %s, description = %s, tags = %s, domain = %s, difficulty = %s, required_roles = %s, stage = %s, repo_link = %s
            WHERE id = %s
        """, (p.title, p.description, json.dumps(p.tags), p.domain, p.difficulty, json.dumps(p.required_roles), p.stage, p.repo_link, project_id))
        conn.commit()
    except HTTPException as he:
        raise he
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
    return {"message": "Project updated"}

@app.delete("/projects/{project_id}")
def delete_project(project_id: int, user_id: int = Query(...)):
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("SELECT owner_id FROM projects WHERE id = %s", (project_id,))
        proj = cur.fetchone()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found")
        if proj['owner_id'] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
            
        cur.execute("DELETE FROM projects WHERE id = %s", (project_id,))
        conn.commit()
    finally:
        conn.close()
    return {"message": "Project deleted"}

# --- TASK / KANBAN ROUTES ---

@app.post("/tasks")
def create_task(t: TaskCreate):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        INSERT INTO tasks (project_id, assigned_to, title, status, priority)
        VALUES (%s, %s, %s, %s, %s) RETURNING id
    """, (t.project_id, t.assigned_to, t.title, t.status, t.priority))
    tid = cur.fetchone()['id']
    conn.commit(); conn.close()
    return {"message": "Task added", "id": tid}

@app.put("/tasks/{task_id}/status")
def update_task_status(task_id: int, status: str):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("UPDATE tasks SET status = %s WHERE id = %s", (status, task_id))
    conn.commit(); conn.close()
    return {"message": "Status updated"}

# --- APPLICATION ROUTES (Matchmaking) ---

@app.post("/applications")
def apply_for_project(a: ApplicationCreate):
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO applications (project_id, applicant_id, role_applied_for, message)
            VALUES (%s, %s, %s, %s)
        """, (a.project_id, a.applicant_id, a.role_applied_for, a.message))
        conn.commit()
        return {"message": "Application sent"}
    except Exception as e:
        conn.rollback()
        return {"error": str(e)} # Duplicate application etc
    finally:
        conn.close()

@app.get("/users/{user_id}/applications")
def get_my_applications(user_id: int):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        SELECT a.*, p.title as project_title 
        FROM applications a
        JOIN projects p ON a.project_id = p.id
        WHERE a.applicant_id = %s
    """, (user_id,))
    apps = cur.fetchall(); conn.close()
    return apps

@app.get("/projects/{project_id}/applications")
def get_project_applications(project_id: int):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        SELECT a.*, u.full_name, u.skills, u.bio
        FROM applications a
        JOIN users u ON a.applicant_id = u.id
        WHERE a.project_id = %s
    """, (project_id,))
    apps = cur.fetchall(); conn.close()
    return apps


# --- MISC ---
@app.get("/")
def read_root():
    return {"message": "Student Idea Hub V2 API Ready"}

# --- CHAT ROUTES ---

@app.get("/projects/{project_id}/chat")
def get_project_chat(project_id: int):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        SELECT c.*, u.full_name as sender_name, u.avatar_url as sender_avatar
        FROM chats c
        JOIN users u ON c.sender_id = u.id
        WHERE c.project_id = %s
        ORDER BY c.created_at ASC
    """, (project_id,))
    messages = cur.fetchall()
    conn.close()
    return messages

@app.post("/projects/{project_id}/chat")
def post_project_chat(project_id: int, chat: ChatMessageCreate):
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO chats (project_id, sender_id, message)
            VALUES (%s, %s, %s) RETURNING id, created_at
        """, (project_id, chat.sender_id, chat.message))
        new_msg = cur.fetchone()
        conn.commit()
        return new_msg
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# --- APPLICATION MANAGEMENT ---

@app.put("/applications/{app_id}/status")
def update_application_status(app_id: int, status: str):
    conn = get_connection(); cur = conn.cursor()
    try:
        # Get App Info
        cur.execute("SELECT * FROM applications WHERE id = %s", (app_id,))
        app = cur.fetchone()
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")
            
        cur.execute("UPDATE applications SET status = %s WHERE id = %s", (status, app_id))
        
        # If Accepted, add to project_members
        if status == 'Accepted':
            # Check if already member
            cur.execute("""
                SELECT * FROM project_members WHERE project_id = %s AND user_id = %s
            """, (app['project_id'], app['applicant_id']))
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO project_members (project_id, user_id, role)
                    VALUES (%s, %s, %s)
                """, (app['project_id'], app['applicant_id'], app['role_applied_for']))
                
        conn.commit()
        return {"message": f"Application {status}"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# --- DIRECT MESSAGING ---

class DirectMessageCreate(BaseModel):
    receiver_id: int
    message: str

@app.post("/messages")
def send_message(msg: DirectMessageCreate, user_id: int = Query(...)):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO direct_messages (sender_id, receiver_id, message)
            VALUES (%s, %s, %s)
            RETURNING id, created_at
        """, (user_id, msg.receiver_id, msg.message))
        new_msg = cur.fetchone()
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()
    return {"status": "Message sent", "id": new_msg['id'], "created_at": new_msg['created_at']}

@app.get("/messages/{other_user_id}")
def get_conversation(other_user_id: int, user_id: int = Query(...)):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT m.*, u.full_name as sender_name, u.avatar_url as sender_avatar, u.phone_number as sender_phone
            FROM direct_messages m
            JOIN users u ON m.sender_id = u.id
            WHERE (sender_id = %s AND receiver_id = %s)
               OR (sender_id = %s AND receiver_id = %s)
            ORDER BY created_at ASC
        """, (user_id, other_user_id, other_user_id, user_id))
        messages = cur.fetchall()
    finally:
        cur.close()
        conn.close()
    return messages

@app.get("/messages/conversations/list")
def get_conversations_list(user_id: int = Query(...)):
    """Get list of users you have chatted with"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Find unique users involved in chats with current user
        cur.execute("""
            SELECT DISTINCT
                CASE WHEN sender_id = %s THEN receiver_id ELSE sender_id END as contact_id
            FROM direct_messages
            WHERE sender_id = %s OR receiver_id = %s
        """, (user_id, user_id, user_id))
        contacts = cur.fetchall()
        
        contact_ids = [c['contact_id'] for c in contacts]
        
        if not contact_ids:
            return []
            
        # Get details for these users
        placeholders = ',' .join(['%s'] * len(contact_ids))
        cur.execute(f"""
            SELECT id, full_name, role, avatar_url, phone_number,
            (SELECT message FROM direct_messages 
             WHERE (sender_id = users.id AND receiver_id = %s) OR (sender_id = %s AND receiver_id = users.id)
             ORDER BY created_at DESC LIMIT 1) as last_message,
             (SELECT created_at FROM direct_messages 
             WHERE (sender_id = users.id AND receiver_id = %s) OR (sender_id = %s AND receiver_id = users.id)
             ORDER BY created_at DESC LIMIT 1) as last_message_time
            FROM users
            WHERE id IN ({placeholders})
            ORDER BY last_message_time DESC
        """, (user_id, user_id, user_id, user_id, *contact_ids))
        
        users_with_last_msg = cur.fetchall()
        
    finally:
        cur.close()
        conn.close()
    return users_with_last_msg

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)