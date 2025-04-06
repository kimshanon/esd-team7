from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class PickerModel(BaseModel):
    firebase_uid: str = Field(..., min_length=1)
    picker_name: str = Field(..., min_length=1)
    picker_email: EmailStr
    picker_phone: int
    is_available: bool = Field(default=True)
    
    # Optional fields you might want to add later
    # location: Optional[str] = None
    # rating: Optional[float] = Field(None, ge=0, le=5)
    
    def to_dict(self):
        """Convert model to dictionary for Firestore storage"""
        return self.model_dump(exclude_none=True)
        
    @classmethod
    def from_dict(cls, data: dict):
        """Create model instance from Firestore document"""
        return cls(**data)