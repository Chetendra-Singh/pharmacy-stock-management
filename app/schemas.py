from pydantic import BaseModel
from datetime import date, datetime
from typing import List, Optional

class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class MedicineBase(BaseModel):
    name: str
    description: Optional[str] = None

class MedicineCreate(MedicineBase):
    pass

class Medicine(MedicineBase):
    id: int
    sellable_stock: Optional[int] = 0
    model_config = {"from_attributes": True}

class BatchCreate(BaseModel):
    medicine_id: int
    quantity: int
    expiry_date: date

class Batch(BatchCreate):
    id: int
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}

class DispenseRequest(BaseModel):
    medicine_id: int
    quantity: int
    course_duration_days: int = 30  # Safety buffer default