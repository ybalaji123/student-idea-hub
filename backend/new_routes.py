
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
