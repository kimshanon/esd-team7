from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class CustomerModel(BaseModel):
    firebase_uid: str = Field(..., min_length=1)
    customer_name: str = Field(..., min_length=1)
    customer_email: EmailStr
    customer_phone: int
    customer_credits: float
    
    # Optional fields that might be useful
    # address: Optional[str] = None
    # customer_notes: Optional[str] = None
    
    def to_dict(self):
        """Convert model to dictionary for Firestore storage"""
        return self.model_dump(exclude_none=True)
        
    @classmethod
    def from_dict(cls, data: dict):
        """Create model instance from Firestore document"""
        return cls(**data)