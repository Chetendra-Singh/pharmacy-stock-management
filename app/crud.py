from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from passlib.context import CryptContext
from . import models, schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(username=user.username, password_hash=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_medicines(db: Session, skip: int = 0, limit: int = 100, search: str = ""):
    query = db.query(models.Medicine)
    if search:
        query = query.filter(models.Medicine.name.ilike(f"%{search}%"))
    
    medicines = query.offset(skip).limit(limit).all()
    
    for med in medicines:
        stock = db.query(func.sum(models.Batch.quantity)).filter(
            models.Batch.medicine_id == med.id,
            models.Batch.expiry_date >= date.today(),
            models.Batch.quantity > 0
        ).scalar()
        med.sellable_stock = stock or 0
    return medicines

def create_medicine(db: Session, medicine: schemas.MedicineCreate):
    db_medicine = models.Medicine(name=medicine.name, description=medicine.description)
    db.add(db_medicine)
    db.commit()
    db.refresh(db_medicine)
    return db_medicine

def create_batch(db: Session, batch: schemas.BatchCreate):
    db_batch = models.Batch(**batch.model_dump())
    db.add(db_batch)
    db.commit()
    db.refresh(db_batch)
    return db_batch

def get_expiring_batches(db: Session, days_threshold: int = 30):
    target_date = date.today() + timedelta(days=days_threshold)
    return db.query(models.Batch).filter(
        models.Batch.expiry_date >= date.today(),
        models.Batch.expiry_date <= target_date,
        models.Batch.quantity > 0
    ).order_by(models.Batch.expiry_date.asc()).all()

def dispense_medicine(db: Session, request: schemas.DispenseRequest):
    safe_expiry_threshold = date.today() + timedelta(days=request.course_duration_days)

    batches = db.query(models.Batch).filter(
        models.Batch.medicine_id == request.medicine_id,
        models.Batch.expiry_date >= safe_expiry_threshold,
        models.Batch.quantity > 0
    ).order_by(models.Batch.expiry_date.asc()).all()

    total_available = sum(b.quantity for b in batches)
    if total_available < request.quantity:
        raise ValueError(f"Insufficient safe stock. Requested: {request.quantity}, Available: {total_available}")

    remaining_to_dispense = request.quantity
    for batch in batches:
        if remaining_to_dispense == 0:
            break
        if batch.quantity <= remaining_to_dispense:
            remaining_to_dispense -= batch.quantity
            batch.quantity = 0 
        else:
            batch.quantity -= remaining_to_dispense
            remaining_to_dispense = 0
            
    db.commit()
    return {"message": f"Successfully dispensed {request.quantity} units.", "remaining_safe_stock": total_available - request.quantity}