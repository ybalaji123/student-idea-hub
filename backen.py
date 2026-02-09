from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import database as db

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- Models ---
class LoginRequest(BaseModel):
    email: str
    password: str

class SignupRequest(BaseModel):
    username: str
    email: str
    password: str

class DevSignupRequest(BaseModel):
    username: str
    email: str
    password: str
    which_dev: str

class IdeaRequest(BaseModel):
    student_id: int
    project_title: str
    description: str
    category: str
    looking_for: str

class DevReqModel(BaseModel):
    student_id: int
    dev_id: int
    idea_id: int

class StatusModel(BaseModel):
    request_id: int
    status: str

class ChatModel(BaseModel):
    request_id: int
    sender_role: str
    message: str

# --- Routes ---
@app.post("/signup")
def signup(req: SignupRequest): return db.register_user(req.username, req.email, req.password)

@app.post("/login")
def login(req: LoginRequest): return db.login_user(req.email, req.password)

@app.post("/dev/signup")
def dev_signup(req: DevSignupRequest): return db.register_developer(req.username, req.email, req.password, req.which_dev)

@app.post("/dev/login")
def dev_login(req: LoginRequest): return db.login_developer(req.email, req.password)

@app.post("/ideas")
def post_idea(req: IdeaRequest): return db.create_idea(req.student_id, req.project_title, req.description, req.category, req.looking_for)

@app.get("/ideas")
def get_ideas(): return db.get_all_ideas()

@app.get("/developers")
def get_devs(): return db.get_all_developers()

@app.post("/send-request")
def send_request(req: DevReqModel): return db.send_dev_request(req.student_id, req.dev_id, req.idea_id)

@app.get("/dev/requests/{dev_id}")
def get_requests(dev_id: int): return db.get_dev_requests(dev_id)

@app.post("/update-request")
def update_request(req: StatusModel): return db.update_request_status(req.request_id, req.status)

@app.get("/check-active-chat/{student_id}")
def check_chat(student_id: int): return db.get_active_request(student_id)

@app.get("/chat/{request_id}")
def get_chat(request_id: int): return db.get_chat_history(request_id)

@app.post("/chat")
def send_chat(req: ChatModel): return db.save_message(req.request_id, req.sender_role, req.message)