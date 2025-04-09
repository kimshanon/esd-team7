from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class PaymentEventType(str, Enum):
    """Enum for payment event types"""
    PAYMENT = "Payment"
    CREDIT_TOPUP = "Credit Top-Up"
    REFUND = "Refund"

class PaymentStatus(str, Enum):
    """Enum for payment status"""
    PENDING = "Pending"
    PAID = "Paid"
    COMPLETED = "Completed"
    FAILED = "Failed"
    REFUNDED = "Refunded"

class PaymentModel(BaseModel):
    """Pydantic model for payment transactions"""
    log_id: str = Field(..., min_length=1)
    customer_id: str = Field(..., min_length=1)
    event_type: str = Field(..., min_length=1)
    event_details: str = Field(..., min_length=1)
    payment_amount: float
    payment_status: str = Field(..., min_length=1)
    timestamp: datetime
    order_id: Optional[str] = None
    payment_id: Optional[str] = None  # Added for when Firestore assigns an ID
    
    def to_dict(self):
        """Convert model to dictionary for Firestore storage"""
        data = self.model_dump(exclude_none=True)
        # Convert datetime to ISO string for Firestore
        if "timestamp" in data:
            data["timestamp"] = data["timestamp"].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create model instance from Firestore document"""
        payment_data = data.copy()
        
        # Convert ISO string timestamp back to datetime
        if "timestamp" in payment_data and isinstance(payment_data["timestamp"], str):
            try:
                payment_data["timestamp"] = datetime.fromisoformat(payment_data["timestamp"])
            except ValueError:
                # Handle potential timezone format issues
                payment_data["timestamp"] = datetime.now()
                
        return cls(**payment_data)
