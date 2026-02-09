import pyodbc

SERVER = r"YEMINENIBALAJI\SQLEXPRESS"
DATABASE = "student_idea_hub"
USERNAME = "sa"
PASSWORD = "yemineni@123"

def get_connection():
    try:
        drivers = pyodbc.drivers()
        driver = "ODBC Driver 18 for SQL Server" if "ODBC Driver 18 for SQL Server" in drivers else "ODBC Driver 17 for SQL Server"
        connection_string = f"DRIVER={{{driver}}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};TrustServerCertificate=yes;"
        return pyodbc.connect(connection_string)
    except Exception as e:
        print("❌ Database Connection Failed:", e)
        return None

# --- AUTH FUNCTIONS ---
def register_user(username, email, password):
    conn = get_connection()
    if not conn: return {"status": False, "message": "DB Failed"}
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO register_user (username, email, Pass) VALUES (?, ?, ?)", (username, email, password))
        conn.commit()
        return {"status": True, "message": "Success"}
    except Exception as e:
        return {"status": False, "message": str(e)}
    finally:
        conn.close()

def login_user(email, password):
    conn = get_connection()
    if not conn: return {"status": False}
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT registerid, username FROM register_user WHERE email = ? AND Pass = ?", (email, password))
        user = cursor.fetchone()
        if user: return {"status": True, "registerid": user[0], "username": user[1]}
        return {"status": False, "message": "Invalid credentials"}
    except Exception as e:
        return {"status": False, "message": str(e)}
    finally:
        conn.close()

def register_developer(username, email, password, which_dev):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO dev_register (username, email, pass, which_dev) VALUES (?, ?, ?, ?)", (username, email, password, which_dev))
        conn.commit()
        return {"status": True}
    except Exception as e:
        return {"status": False, "message": str(e)}

def login_developer(email, password):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT devid, username, which_dev, email FROM dev_register WHERE email = ? AND pass = ?", (email, password))
        user = cursor.fetchone()
        if user: return {"status": True, "devid": user[0], "username": user[1], "which_dev": user[2]}
        return {"status": False, "message": "Invalid credentials"}
    except Exception as e:
        return {"status": False, "message": str(e)}

# --- IDEA FUNCTIONS ---
def create_idea(student_id, title, desc, category, looking_for):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ideas (student_id, project_title, description, category, looking_for) VALUES (?, ?, ?, ?, ?)", 
                   (student_id, title, desc, category, looking_for))
    conn.commit()
    conn.close()
    return {"status": True}

def get_all_ideas():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ideas ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"idea_id": r[0], "title": r[2], "description": r[3], "category": r[4], "status": "open"} for r in rows]

def get_all_developers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT devid, username, which_dev FROM dev_register")
    rows = cursor.fetchall()
    conn.close()
    return [{"devid": r[0], "username": r[1], "type": r[2]} for r in rows]

# --- REQUEST & CHAT FUNCTIONS ---
def send_dev_request(student_id, dev_id, idea_id):
    conn = get_connection()
    cursor = conn.cursor()
    # Check if exists
    cursor.execute("SELECT request_id FROM dev_requests WHERE student_id=? AND dev_id=? AND idea_id=?", (student_id, dev_id, idea_id))
    if cursor.fetchone(): return {"status": False, "message": "Already Requested"}
    
    cursor.execute("INSERT INTO dev_requests (student_id, dev_id, idea_id) VALUES (?, ?, ?)", (student_id, dev_id, idea_id))
    conn.commit()
    conn.close()
    return {"status": True}

def get_dev_requests(dev_id):
    conn = get_connection()
    cursor = conn.cursor()
    # JOIN TABLES TO GET FULL DETAILS (Student Name, Email, Idea Title, Description)
    query = """
        SELECT r.request_id, u.username, u.email, i.project_title, i.description, r.status, r.student_id
        FROM dev_requests r
        JOIN register_user u ON r.student_id = u.registerid
        JOIN ideas i ON r.idea_id = i.idea_id
        WHERE r.dev_id = ?
    """
    cursor.execute(query, (dev_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{
        "request_id": r[0], "student_name": r[1], "student_email": r[2],
        "project_title": r[3], "project_desc": r[4], "status": r[5], "student_id": r[6]
    } for r in rows]

def update_request_status(request_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE dev_requests SET status = ? WHERE request_id = ?", (status, request_id))
    conn.commit()
    conn.close()
    return {"status": True}

def save_message(request_id, role, message):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_messages (request_id, sender_role, message_text) VALUES (?, ?, ?)", (request_id, role, message))
    conn.commit()
    conn.close()
    return {"status": True}

def get_chat_history(request_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT sender_role, message_text FROM chat_messages WHERE request_id = ? ORDER BY sent_at ASC", (request_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"sender": r[0], "text": r[1]} for r in rows]

def get_active_request(student_id):
    conn = get_connection()
    cursor = conn.cursor()
    # Find a request that has been ACCEPTED
    cursor.execute("SELECT request_id, dev_id FROM dev_requests WHERE student_id = ? AND status = 'accepted'", (student_id,))
    row = cursor.fetchone()
    conn.close()
    if row: return {"request_id": row[0], "dev_id": row[1]}
    return None