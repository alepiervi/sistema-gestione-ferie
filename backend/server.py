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

async def calculate_used_vacation_days(user_id: str, year: int) -> int:
    """Calculate used vacation days for a user in a specific year"""
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31, 23, 59, 59)
    
    requests = await db.requests.find({
        "user_id": user_id,
        "type": "ferie",
        "status": "approved",
        "created_at": {"$gte": start_date, "$lte": end_date}
    }).to_list(None)
    
    total_days = 0
    for req in requests:
        if req.get('start_date') and req.get('end_date'):
            start = datetime.fromisoformat(req['start_date']) if isinstance(req['start_date'], str) else req['start_date']
            end = datetime.fromisoformat(req['end_date']) if isinstance(req['end_date'], str) else req['end_date']
            total_days += (end - start).days + 1
    
    return total_days

async def get_or_create_vacation_allowance(user_id: str, year: int, default_max_days: int = 20):
    """Get existing vacation allowance or create new one"""
    allowance = await db.vacation_allowances.find_one({"user_id": user_id, "year": year})
    
    if not allowance:
        # Calculate used days for the year
        used_days = await calculate_used_vacation_days(user_id, year)
        
        # Calculate carried over days from previous year
        carried_over_days = 0
        prev_year_allowance = await db.vacation_allowances.find_one({"user_id": user_id, "year": year - 1})
        if prev_year_allowance:
            carried_over_days = max(0, prev_year_allowance['remaining_days'])
        
        # Create new allowance
        allowance_data = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "year": year,
            "max_days": default_max_days,
            "used_days": used_days,
            "carried_over_days": carried_over_days,
            "remaining_days": default_max_days + carried_over_days - used_days,
            "created_at": datetime.utcnow()
        }
        
        await db.vacation_allowances.insert_one(allowance_data)
        allowance = allowance_data
    
    return allowance

async def recalculate_vacation_allowance(user_id: str, year: int):
    """Recalculate vacation allowance for a specific year"""
    allowance = await db.vacation_allowances.find_one({"user_id": user_id, "year": year})
    if not allowance:
        return await get_or_create_vacation_allowance(user_id, year)
    
    # Recalculate used days
    used_days = await calculate_used_vacation_days(user_id, year)
    
    # Calculate remaining days
    remaining_days = allowance['max_days'] + allowance['carried_over_days'] - used_days
    
    # Update allowance
    await db.vacation_allowances.update_one(
        {"user_id": user_id, "year": year},
        {
            "$set": {
                "used_days": used_days,
                "remaining_days": remaining_days,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Update next year's carried over days if exists
    next_year_allowance = await db.vacation_allowances.find_one({"user_id": user_id, "year": year + 1})
    if next_year_allowance:
        can_carry_over = max(0, remaining_days)
        await db.vacation_allowances.update_one(
            {"user_id": user_id, "year": year + 1},
            {
                "$set": {
                    "carried_over_days": can_carry_over,
                    "remaining_days": next_year_allowance['max_days'] + can_carry_over - next_year_allowance['used_days'],
                    "updated_at": datetime.utcnow()
                }
            }
        )
    
    return await db.vacation_allowances.find_one({"user_id": user_id, "year": year})

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
    
    # Remove MongoDB's _id field if present
    if '_id' in request_doc:
        del request_doc['_id']
    
    # Update request
    status = "approved" if response.action == "approve" else "rejected"
    update_data = {
        "status": status,
        "admin_notes": response.notes,
        "updated_at": datetime.utcnow()
    }
    
    await db.requests.update_one({"id": request_id}, {"$set": update_data})
    
    # Recalculate vacation allowances if it's a vacation request
    await update_vacation_on_request_change(request_doc['user_id'], request_doc['type'])
    
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

# Employee update request (only if pending)
@api_router.put("/requests/{request_id}")
async def update_request(
    request_id: str,
    request_data: LeaveRequestCreate,
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "employee":
        raise HTTPException(status_code=403, detail="Solo i dipendenti possono modificare le richieste")
    
    # Find existing request
    existing_request = await db.requests.find_one({"id": request_id, "user_id": current_user.id})
    if not existing_request:
        raise HTTPException(status_code=404, detail="Richiesta non trovata")
    
    # Check if request is still pending
    if existing_request.get('status', 'pending') != 'pending':
        raise HTTPException(status_code=400, detail="Non puoi modificare una richiesta già elaborata")
    
    # Create updated request object
    updated_request = LeaveRequest(
        id=request_id,
        user_id=current_user.id,
        **request_data.dict()
    )
    
    # Convert to dict and handle date serialization
    request_dict = updated_request.dict()
    for field in ['start_date', 'end_date', 'permit_date', 'sick_start_date']:
        if request_dict.get(field) is not None:
            if hasattr(request_dict[field], 'isoformat'):
                request_dict[field] = request_dict[field].isoformat()
    
    for field in ['start_time', 'end_time']:
        if request_dict.get(field) is not None:
            if hasattr(request_dict[field], 'isoformat'):
                request_dict[field] = request_dict[field].isoformat()
    
    # Update the request
    request_dict['updated_at'] = datetime.utcnow()
    await db.requests.update_one({"id": request_id}, {"$set": request_dict})
    
    return {"message": "Richiesta modificata con successo"}

# Employee delete request (only if pending)
@api_router.delete("/requests/{request_id}")
async def delete_request(
    request_id: str,
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "employee":
        raise HTTPException(status_code=403, detail="Solo i dipendenti possono cancellare le richieste")
    
    # Find existing request
    existing_request = await db.requests.find_one({"id": request_id, "user_id": current_user.id})
    if not existing_request:
        raise HTTPException(status_code=404, detail="Richiesta non trovata")
    
    # Check if request is still pending
    if existing_request.get('status', 'pending') != 'pending':
        raise HTTPException(status_code=400, detail="Non puoi cancellare una richiesta già elaborata")
    
    # Delete the request
    await db.requests.delete_one({"id": request_id})
    
    return {"message": "Richiesta cancellata con successo"}

# Get employee stats (admin only)
@api_router.get("/admin/employees/{employee_id}/stats")
async def get_employee_stats(
    employee_id: str,
    year: int = datetime.now().year,
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accesso negato")
    
    # Check if employee exists
    employee = await db.users.find_one({"id": employee_id, "role": "employee"})
    if not employee:
        raise HTTPException(status_code=404, detail="Dipendente non trovato")
    
    # Get all approved requests for the employee in the specified year
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31, 23, 59, 59)
    
    pipeline = [
        {
            "$match": {
                "user_id": employee_id,
                "status": "approved",
                "created_at": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }
        },
        {
            "$group": {
                "_id": "$type",
                "count": {"$sum": 1},
                "days": {
                    "$sum": {
                        "$switch": {
                            "branches": [
                                {"case": {"$eq": ["$type", "ferie"]}, "then": {"$add": [{"$subtract": [{"$dateFromString": {"dateString": "$end_date"}}, {"$dateFromString": {"dateString": "$start_date"}}]}, 86400000]}},
                                {"case": {"$eq": ["$type", "malattia"]}, "then": "$sick_days"}
                            ],
                            "default": 0
                        }
                    }
                }
            }
        }
    ]
    
    # Simplified approach - get all requests and calculate in Python
    requests = await db.requests.find({
        "user_id": employee_id,
        "status": "approved",
        "created_at": {"$gte": start_date, "$lte": end_date}
    }).to_list(None)
    
    ferie_days = 0
    permessi_count = 0
    malattie_days = 0
    
    for req in requests:
        if req['type'] == 'ferie':
            # Calculate days between start_date and end_date
            if req.get('start_date') and req.get('end_date'):
                start = datetime.fromisoformat(req['start_date']) if isinstance(req['start_date'], str) else req['start_date']
                end = datetime.fromisoformat(req['end_date']) if isinstance(req['end_date'], str) else req['end_date']
                ferie_days += (end - start).days + 1
        elif req['type'] == 'permesso':
            permessi_count += 1
        elif req['type'] == 'malattia':
            malattie_days += req.get('sick_days', 0)
    
    return {
        "employee": {
            "id": employee['id'],
            "username": employee['username'],
            "email": employee['email']
        },
        "year": year,
        "stats": {
            "ferie_days": ferie_days,
            "permessi_count": permessi_count,
            "malattie_days": malattie_days,
            "total_requests": len(requests)
        }
    }

# Get available years for employee stats
@api_router.get("/admin/employees/{employee_id}/years")
async def get_employee_years(
    employee_id: str,
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accesso negato")
    
    # Get all years where the employee has requests
    pipeline = [
        {"$match": {"user_id": employee_id}},
        {"$group": {"_id": {"$year": "$created_at"}}},
        {"$sort": {"_id": -1}}
    ]
    
    years_result = await db.requests.aggregate(pipeline).to_list(None)
    years = [item['_id'] for item in years_result]
    
    # Always include current year
    current_year = datetime.now().year
    if current_year not in years:
        years.insert(0, current_year)
    
    return {"years": sorted(years, reverse=True)}

# Get personal stats (employee)
@api_router.get("/stats")
async def get_personal_stats(
    year: int = datetime.now().year,
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "employee":
        raise HTTPException(status_code=403, detail="Solo i dipendenti possono vedere le proprie statistiche")
    
    # Get all approved requests for the current user in the specified year
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31, 23, 59, 59)
    
    requests = await db.requests.find({
        "user_id": current_user.id,
        "status": "approved",
        "created_at": {"$gte": start_date, "$lte": end_date}
    }).to_list(None)
    
    ferie_days = 0
    permessi_count = 0
    malattie_days = 0
    
    for req in requests:
        if req['type'] == 'ferie':
            if req.get('start_date') and req.get('end_date'):
                start = datetime.fromisoformat(req['start_date']) if isinstance(req['start_date'], str) else req['start_date']
                end = datetime.fromisoformat(req['end_date']) if isinstance(req['end_date'], str) else req['end_date']
                ferie_days += (end - start).days + 1
        elif req['type'] == 'permesso':
            permessi_count += 1
        elif req['type'] == 'malattia':
            malattie_days += req.get('sick_days', 0)
    
    return {
        "year": year,
        "stats": {
            "ferie_days": ferie_days,
            "permessi_count": permessi_count,
            "malattie_days": malattie_days,
            "total_requests": len(requests)
        }
    }

# Get available years for personal stats
@api_router.get("/years")
async def get_personal_years(current_user: User = Depends(get_current_user)):
    if current_user.role != "employee":
        raise HTTPException(status_code=403, detail="Solo i dipendenti possono vedere le proprie statistiche")
    
    # Get all years where the user has requests
    pipeline = [
        {"$match": {"user_id": current_user.id}},
        {"$group": {"_id": {"$year": "$created_at"}}},
        {"$sort": {"_id": -1}}
    ]
    
    years_result = await db.requests.aggregate(pipeline).to_list(None)
    years = [item['_id'] for item in years_result]
    
    # Always include current year
    current_year = datetime.now().year
    if current_year not in years:
        years.insert(0, current_year)
    
    return {"years": sorted(years, reverse=True)}

# Vacation allowance management
@api_router.get("/admin/employees/{employee_id}/vacation-summary")
async def get_employee_vacation_summary(
    employee_id: str,
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accesso negato")
    
    # Check if employee exists
    employee = await db.users.find_one({"id": employee_id, "role": "employee"})
    if not employee:
        raise HTTPException(status_code=404, detail="Dipendente non trovato")
    
    # Get all vacation allowances for the employee
    allowances = await db.vacation_allowances.find({"user_id": employee_id}).sort("year", -1).to_list(None)
    
    # Get current year and ensure it exists
    current_year = datetime.now().year
    current_allowance = await get_or_create_vacation_allowance(employee_id, current_year)
    
    # Ensure current year is included
    years_in_db = {a['year'] for a in allowances}
    if current_year not in years_in_db:
        allowances.insert(0, current_allowance)
        allowances.sort(key=lambda x: x['year'], reverse=True)
    
    # Calculate totals
    total_remaining = sum(max(0, a['remaining_days']) for a in allowances)
    total_used_this_year = current_allowance['used_days']
    
    return {
        "employee": {
            "id": employee['id'],
            "username": employee['username'],
            "email": employee['email']
        },
        "current_year": current_year,
        "total_remaining_days": total_remaining,
        "used_this_year": total_used_this_year,
        "vacation_by_year": [
            {
                "year": a['year'],
                "max_days": a['max_days'],
                "used_days": a['used_days'],
                "carried_over_days": a['carried_over_days'],
                "remaining_days": a['remaining_days'],
                "can_carry_over": max(0, a['remaining_days']) if a['year'] < current_year else a['remaining_days']
            }
            for a in allowances
        ]
    }

@api_router.put("/admin/employees/{employee_id}/vacation-allowance/{year}")
async def update_vacation_allowance(
    employee_id: str,
    year: int,
    allowance_data: dict,
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accesso negato")
    
    # Validate data
    max_days = allowance_data.get('max_days')
    if max_days is None or max_days < 0 or max_days > 50:
        raise HTTPException(status_code=400, detail="Giorni massimi devono essere tra 0 e 50")
    
    # Get or create allowance
    allowance = await get_or_create_vacation_allowance(employee_id, year, max_days)
    
    # Update max days
    await db.vacation_allowances.update_one(
        {"user_id": employee_id, "year": year},
        {
            "$set": {
                "max_days": max_days,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Recalculate all affected years
    await recalculate_vacation_allowance(employee_id, year)
    
    # If this is not the current year, recalculate subsequent years
    current_year = datetime.now().year
    if year < current_year:
        for future_year in range(year + 1, current_year + 1):
            future_allowance = await db.vacation_allowances.find_one({"user_id": employee_id, "year": future_year})
            if future_allowance:
                await recalculate_vacation_allowance(employee_id, future_year)
    
    return {"message": "Giorni ferie aggiornati con successo"}

@api_router.get("/vacation-summary")
async def get_personal_vacation_summary(current_user: User = Depends(get_current_user)):
    if current_user.role != "employee":
        raise HTTPException(status_code=403, detail="Solo i dipendenti possono vedere le proprie ferie")
    
    # Get all vacation allowances for the user
    allowances = await db.vacation_allowances.find({"user_id": current_user.id}).sort("year", -1).to_list(None)
    
    # Get current year and ensure it exists
    current_year = datetime.now().year
    current_allowance = await get_or_create_vacation_allowance(current_user.id, current_year)
    
    # Ensure current year is included
    years_in_db = {a['year'] for a in allowances}
    if current_year not in years_in_db:
        allowances.insert(0, current_allowance)
        allowances.sort(key=lambda x: x['year'], reverse=True)
    
    # Calculate totals
    total_remaining = sum(max(0, a['remaining_days']) for a in allowances)
    total_used_this_year = current_allowance['used_days']
    
    return {
        "current_year": current_year,
        "total_remaining_days": total_remaining,
        "used_this_year": total_used_this_year,
        "vacation_by_year": [
            {
                "year": a['year'],
                "max_days": a['max_days'],
                "used_days": a['used_days'],
                "carried_over_days": a['carried_over_days'],
                "remaining_days": a['remaining_days'],
                "can_carry_over": max(0, a['remaining_days']) if a['year'] < current_year else a['remaining_days']
            }
            for a in allowances
        ]
    }

# Automatically recalculate vacation allowances when vacation requests are approved/rejected
async def update_vacation_on_request_change(user_id: str, request_type: str):
    """Update vacation allowances when requests change"""
    if request_type != "ferie":
        return
    
    # Get all years that might be affected
    current_year = datetime.now().year
    years_to_update = []
    
    # Find all years with vacation requests for this user
    pipeline = [
        {"$match": {"user_id": user_id, "type": "ferie", "status": "approved"}},
        {"$group": {"_id": {"$year": "$created_at"}}},
    ]
    
    years_result = await db.requests.aggregate(pipeline).to_list(None)
    request_years = [item['_id'] for item in years_result]
    
    # Always include current year
    request_years.append(current_year)
    years_to_update = sorted(set(request_years))
    
    # Recalculate each year
    for year in years_to_update:
        await recalculate_vacation_allowance(user_id, year)

class YearlyStats(BaseModel):
    year: int
    ferie_days: int
    permessi_count: int
    malattie_days: int
    total_requests: int

class VacationAllowance(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    year: int
    max_days: int = 20  # Giorni ferie massimi per l'anno
    used_days: int = 0  # Giorni utilizzati
    carried_over_days: int = 0  # Giorni riportati dall'anno precedente
    remaining_days: int = 20  # Giorni rimanenti (max_days + carried_over - used_days)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class VacationAllowanceCreate(BaseModel):
    user_id: str
    year: int
    max_days: int
    
    @validator('max_days')
    def validate_max_days(cls, v):
        if v < 0 or v > 50:
            raise ValueError('I giorni massimi devono essere tra 0 e 50')
        return v

class VacationSummary(BaseModel):
    year: int
    max_days: int
    used_days: int
    carried_over_days: int
    remaining_days: int
    can_carry_over: int  # Giorni che possono essere riportati all'anno successivo

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
    import os
# ... altro codice ...

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run("server:app", host="0.0.0.0", port=port)
