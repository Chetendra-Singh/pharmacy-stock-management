from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
from jose import JWTError, jwt
import os

from . import models, schemas, crud, database

# JWT Settings
SECRET_KEY = "pharmacy_super_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI(title="Pharmacy Inventory API")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = crud.get_user_by_username(db, username=username)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# --- Auth Routes ---
@app.post("/api/register", response_model=schemas.Token)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    crud.create_user(db=db, user=user)
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not crud.pwd_context.verify(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# --- Business Routes (Protected) ---
@app.get("/api/medicines", response_model=list[schemas.Medicine])
def read_medicines(skip: int = 0, limit: int = 10, search: str = "", db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    return crud.get_medicines(db, skip=skip, limit=limit, search=search)

@app.post("/api/medicines", response_model=schemas.Medicine)
def create_medicine(medicine: schemas.MedicineCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    return crud.create_medicine(db=db, medicine=medicine)

@app.post("/api/batches", response_model=schemas.Batch)
def create_batch(batch: schemas.BatchCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    return crud.create_batch(db=db, batch=batch)

@app.get("/api/medicines/{medicine_id}/batches", response_model=list[schemas.Batch])
def get_medicine_batches(medicine_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Batch).filter(
        models.Batch.medicine_id == medicine_id, 
        models.Batch.quantity > 0
    ).order_by(models.Batch.expiry_date.asc()).all()

@app.post("/api/dispense")
def dispense_medicine(request: schemas.DispenseRequest, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    try:
        return crud.dispense_medicine(db=db, request=request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/alerts/expiring")
def expiring_alerts(days: int = 30, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    return crud.get_expiring_batches(db=db, days_threshold=days)

# --- Frontend Serving & Startup Seeding ---
@app.on_event("startup")
def seed_data():
    db = database.SessionLocal()
    if not db.query(models.User).first():
        # Seed Pharmacist
        crud.create_user(db, schemas.UserCreate(username="admin", password="password"))
        # Seed Medicines
        med1 = models.Medicine(name="Paracetamol 500mg", description="Pain reliever")
        med2 = models.Medicine(name="Amoxicillin 250mg", description="Antibiotic")
        db.add_all([med1, med2])
        db.commit()
        # Seed Batches
        db.add_all([
            models.Batch(medicine_id=med1.id, quantity=100, expiry_date=date.today() + timedelta(days=5)), 
            models.Batch(medicine_id=med1.id, quantity=500, expiry_date=date.today() + timedelta(days=365)), 
            models.Batch(medicine_id=med2.id, quantity=50, expiry_date=date.today() - timedelta(days=10)), 
            models.Batch(medicine_id=med2.id, quantity=200, expiry_date=date.today() + timedelta(days=400)) 
        ])
        db.commit()
    db.close()

if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/", StaticFiles(directory="static", html=True), name="static")