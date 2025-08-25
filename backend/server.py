from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta, date, time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import jwt
import hashlib
from passlib.context import CryptContext
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"

# Create the main app
app = FastAPI(title="Sistema Gestione Ferie e Permessi", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Email Configuration
class EmailSettings:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.smtp_use_tls = True
        self.admin_email = os.environ.get('ADMIN_EMAIL', '')  # To be configured manually
        self.admin_password = os.environ.get('ADMIN_APP_PASSWORD', '')  # Gmail App Password
        self.from_name = "Sistema Gestione Ferie"

email_settings = EmailSettings()

# ===== MODELS =====

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: EmailStr
    password_hash: str
    role: str = "employee"  # "admin" or "employee"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username deve essere almeno 3 caratteri')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password deve essere almeno 6 caratteri')
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class LeaveRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    type: str  # "ferie", "permesso", "malattia"
    
    # For Ferie (Vacations)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # For Permessi (Time off)
    permit_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    
    # For Malattia (Sick leave)
    sick_start_date: Optional[date] = None
    sick_days: Optional[int] = None
    protocol_code: Optional[str] = None
    
    status: str = "pending"  # "pending", "approved", "rejected"
    admin_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class LeaveRequestCreate(BaseModel):
    type: str
    
    # For Ferie
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # For Permessi
    permit_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    
    # For Malattia
    sick_start_date: Optional[date] = None
    sick_days: Optional[int] = None
    protocol_code: Optional[str] = None
    
    @validator('type')
    def validate_type(cls, v):
        if v not in ['ferie', 'permesso', 'malattia']:
            raise ValueError('Tipo deve essere: ferie, permesso, o malattia')
        return v
    
    @validator('end_date')
    def validate_vacation_dates(cls, v, values):
        if values.get('type') == 'ferie':
            if not v or not values.get('start_date'):
                raise ValueError('Date di inizio e fine sono richieste per le ferie')
            if v < values.get('start_date'):
                raise ValueError('Data di fine deve essere dopo la data di inizio')
            
            # Check max 15 consecutive days
            days_diff = (v - values.get('start_date')).days + 1
            if days_diff > 15:
                raise ValueError('Massimo 15 giorni consecutivi per le ferie')
        return v

class AdminResponse(BaseModel):
    request_id: str
    action: str  # "approve" or "reject"
    notes: Optional[str] = None

class DashboardStats(BaseModel):
    pending_ferie: int
    pending_permessi: int
    pending_malattie: int
    total_pending: int

class AdminSettings(BaseModel):
    email: EmailStr

# ===== UTILITY FUNCTIONS =====

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=30)  # Long-lived token
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token invalido")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token invalido")
    
    user = await db.users.find_one({"id": user_id})
    if user is None:
        raise HTTPException(status_code=401, detail="Utente non trovato")
    return User(**user)

async def send_email(to_email: str, subject: str, body: str, html_body: str = None):
    """Send email using SMTP Gmail"""
    try:
        if not email_settings.admin_email or not email_settings.admin_password:
            logging.warning("Email credentials not configured")
            return False
        
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{email_settings.from_name} <{email_settings.admin_email}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add plain text
        text_part = MIMEText(body, 'plain', 'utf-8')
        msg.attach(text_part)
        
        # Add HTML if provided
        if html_body:
            html_part = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(html_part)
        
        # Send email
        server = smtplib.SMTP(email_settings.smtp_server, email_settings.smtp_port)
        server.starttls()
        server.login(email_settings.admin_email, email_settings.admin_password)
        server.send_message(msg)
        server.quit()
        
        logging.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
        return False

# ===== ROUTES =====

@api_router.get("/")
async def root():
    return {"message": "Sistema Gestione Ferie e Permessi API", "version": "1.0.0"}

# Initialize admin user
@app.on_event("startup")
async def create_admin_user():
    """Create default admin user if not exists"""
    admin_user = await db.users.find_one({"role": "admin"})
    if not admin_user:
        admin_password = "admin123"  # Default password - should be changed
        admin_data = {
            "id": str(uuid.uuid4()),
            "username": "admin",
            "email": "admin@company.com",
            "password_hash": hash_password(admin_password),
            "role": "admin",
            "created_at": datetime.utcnow(),
            "is_active": True
        }
        await db.users.insert_one(admin_data)
        logging.info("Admin user created - Username: admin, Password: admin123")

# Authentication
@api_router.post("/login")
async def login(user_data: UserLogin):
    user = await db.users.find_one({"username": user_data.username, "is_active": True})
    if not user or not verify_password(user_data.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Username o password non corretti")
    
    access_token = create_access_token(data={"sub": user['id'], "role": user['role']})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user['id'],
            "username": user['username'],
            "email": user['email'],
            "role": user['role']
        }
    }

# Admin routes - Create employees
@api_router.post("/admin/employees")
async def create_employee(
    employee_data: UserCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo gli amministratori possono creare dipendenti")
    
    # Check if username or email already exists
    existing = await db.users.find_one({
        "$or": [
            {"username": employee_data.username},
            {"email": employee_data.email}
        ]
    })
    if existing:
        raise HTTPException(status_code=400, detail="Username o email già esistente")
    
    # Create new employee
    employee = User(
        username=employee_data.username,
        email=employee_data.email,
        password_hash=hash_password(employee_data.password),
        role="employee"
    )
    
    await db.users.insert_one(employee.dict())
    
    # Send credentials email
    subject = "Credenziali di accesso - Sistema Gestione Ferie"
    body = f"""
    Ciao {employee_data.username},
    
    È stato creato un account per te nel sistema di gestione ferie e permessi.
    
    Le tue credenziali di accesso sono:
    Username: {employee_data.username}
    Password: {employee_data.password}
    
    Puoi accedere al sistema utilizzando queste credenziali.
    
    Cordiali saluti,
    Amministrazione
    """
    
    html_body = f"""
    <h2>Benvenuto nel Sistema Gestione Ferie</h2>
    <p>Ciao <strong>{employee_data.username}</strong>,</p>
    <p>È stato creato un account per te nel sistema di gestione ferie e permessi.</p>
    <div style="background: #f5f5f5; padding: 15px; margin: 15px 0; border-radius: 5px;">
        <h3>Le tue credenziali:</h3>
        <p><strong>Username:</strong> {employee_data.username}</p>
        <p><strong>Password:</strong> {employee_data.password}</p>
    </div>
    <p>Puoi accedere al sistema utilizzando queste credenziali.</p>
    <p>Cordiali saluti,<br>Amministrazione</p>
    """
    
    background_tasks.add_task(send_email, employee_data.email, subject, body, html_body)
    
    return {"message": "Dipendente creato con successo", "employee_id": employee.id}

# Get employees (admin only)
@api_router.get("/admin/employees")
async def get_employees(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accesso negato")
    
    employees = await db.users.find({"role": "employee"}).to_list(1000)
    return [{"id": emp['id'], "username": emp['username'], "email": emp['email'], 
             "created_at": emp['created_at'], "is_active": emp['is_active']} for emp in employees]

# Employee requests
@api_router.post("/requests")
async def create_request(
    request_data: LeaveRequestCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "employee":
        raise HTTPException(status_code=403, detail="Solo i dipendenti possono fare richieste")
    
    # Create request
    request_obj = LeaveRequest(
        user_id=current_user.id,
        **request_data.dict()
    )
    
    # Convert the request to dict and handle date serialization for MongoDB
    request_dict = request_obj.dict()
    
    # Convert date objects to ISO strings for MongoDB storage
    for field in ['start_date', 'end_date', 'permit_date', 'sick_start_date']:
        if request_dict.get(field) is not None:
            if hasattr(request_dict[field], 'isoformat'):
                request_dict[field] = request_dict[field].isoformat()
    
    # Convert time objects to strings for MongoDB storage
    for field in ['start_time', 'end_time']:
        if request_dict.get(field) is not None:
            if hasattr(request_dict[field], 'isoformat'):
                request_dict[field] = request_dict[field].isoformat()
    
    await db.requests.insert_one(request_dict)
    
    # Send notification to admin
    if email_settings.admin_email:
        subject = f"Nuova richiesta {request_data.type} - {current_user.username}"
        body = f"""
        È stata ricevuta una nuova richiesta di {request_data.type} da {current_user.username}.
        
        Dettagli richiesta:
        Tipo: {request_data.type}
        Dipendente: {current_user.username} ({current_user.email})
        Data richiesta: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        
        Accedi al sistema per gestire la richiesta.
        """
        
        background_tasks.add_task(send_email, email_settings.admin_email, subject, body)
    
    return {"message": "Richiesta creata con successo", "request_id": request_obj.id}

# Get user requests
@api_router.get("/requests")
async def get_user_requests(current_user: User = Depends(get_current_user)):
    if current_user.role == "admin":
        # Admin sees all requests
        requests = await db.requests.find().sort("created_at", -1).to_list(1000)
    else:
        # Employee sees only their requests
        requests = await db.requests.find({"user_id": current_user.id}).sort("created_at", -1).to_list(1000)
    
    # Clean up MongoDB ObjectId and convert to JSON-serializable format
    for req in requests:
        # Remove MongoDB's _id field if present
        if '_id' in req:
            del req['_id']
        
        # Add user info for admin view
        if current_user.role == "admin":
            user = await db.users.find_one({"id": req['user_id']})
            if user:
                req['username'] = user['username']
                req['user_email'] = user['email']
    
    return requests

# Admin dashboard stats
@api_router.get("/admin/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accesso negato")
    
    pending_ferie = await db.requests.count_documents({"type": "ferie", "status": "pending"})
    pending_permessi = await db.requests.count_documents({"type": "permesso", "status": "pending"})
    pending_malattie = await db.requests.count_documents({"type": "malattia", "status": "pending"})
    
    return DashboardStats(
        pending_ferie=pending_ferie,
        pending_permessi=pending_permessi,
        pending_malattie=pending_malattie,
        total_pending=pending_ferie + pending_permessi + pending_malattie
    )

# Admin respond to request
@api_router.put("/admin/requests/{request_id}")
async def respond_to_request(
    request_id: str,
    response: AdminResponse,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accesso negato")
    
    # Find request
    request_doc = await db.requests.find_one({"id": request_id})
    if not request_doc:
        raise HTTPException(status_code=404, detail="Richiesta non trovata")
    
    # Update request
    status = "approved" if response.action == "approve" else "rejected"
    update_data = {
        "status": status,
        "admin_notes": response.notes,
        "updated_at": datetime.utcnow()
    }
    
    await db.requests.update_one({"id": request_id}, {"$set": update_data})
    
    # Send notification to employee
    user = await db.users.find_one({"id": request_doc['user_id']})
    if user:
        action_text = "approvata" if status == "approved" else "rifiutata"
        subject = f"Richiesta {request_doc['type']} {action_text}"
        
        body = f"""
        Ciao {user['username']},
        
        La tua richiesta di {request_doc['type']} è stata {action_text}.
        
        Data richiesta: {request_doc['created_at']}
        Stato: {action_text.upper()}
        """
        
        if response.notes:
            body += f"\n\nNote dell'amministratore:\n{response.notes}"
        
        body += "\n\nCordiali saluti,\nAmministrazione"
        
        background_tasks.add_task(send_email, user['email'], subject, body)
    
    return {"message": f"Richiesta {status} con successo"}

# Admin settings - Change email
@api_router.put("/admin/settings")
async def update_admin_settings(
    settings: AdminSettings,
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accesso negato")
    
    # Update admin email in database
    await db.users.update_one(
        {"id": current_user.id},
        {"$set": {"email": settings.email}}
    )
    
    return {"message": "Impostazioni aggiornate con successo"}

# Change password
@api_router.put("/change-password")
async def change_password(
    password_data: dict,
    current_user: User = Depends(get_current_user)
):
    current_password = password_data.get('current_password')
    new_password = password_data.get('new_password')
    
    if not current_password or not new_password:
        raise HTTPException(status_code=400, detail="Password corrente e nuova password richieste")
    
    # Verify current password
    user_doc = await db.users.find_one({"id": current_user.id})
    if not verify_password(current_password, user_doc['password_hash']):
        raise HTTPException(status_code=400, detail="Password corrente non corretta")
    
    # Update password
    new_hash = hash_password(new_password)
    await db.users.update_one(
        {"id": current_user.id},
        {"$set": {"password_hash": new_hash}}
    )
    
    return {"message": "Password cambiata con successo"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()