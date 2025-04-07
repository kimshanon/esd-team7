from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class OrderStatus(str, Enum):
    pending = "pending"
    assigned = "assigned"
    preparing = "preparing"
    delivering = "delivering"
    completed = "completed"
    cancelled = "cancelled"

class OrderItemModel(BaseModel):
    order_item: str = Field(..., min_length=1)
    order_quantity: int = Field(..., gt=0)
    order_price: float = Field(..., gt=0)
    
    def to_dict(self):
        """Convert model to dictionary for Firestore storage"""
        return self.model_dump(exclude_none=True)
        
    @classmethod
    def from_dict(cls, data: dict):
        """Create model instance from Firestore document"""
        return cls(**data)

class OrderModel(BaseModel):
    customer_id: str = Field(..., min_length=1)
    picker_id: Optional[str] = None
    stall_id: str = Field(..., min_length=1)
    order_status: OrderStatus = Field(default=OrderStatus.pending)
    order_location: str = Field(..., min_length=1)
    order_start: datetime = Field(default_factory=datetime.now)
    order_completed: Optional[datetime] = None
    is_paid: bool = Field(default=False)
    order_items: List[OrderItemModel] = Field(..., min_items=1)
    
    def to_dict(self):
        """Convert model to dictionary for Firestore storage"""
        # Convert datetime objects to ISO strings for Firestore
        data = self.model_dump(exclude={"order_items"}, exclude_none=True)
        if "order_start" in data:
            data["order_start"] = data["order_start"].isoformat()
        if "order_completed" in data and data["order_completed"]:
            data["order_completed"] = data["order_completed"].isoformat()
        return data
        
    @classmethod
    def from_dict(cls, data: dict, items=None):
        """Create model instance from Firestore document and optional items list"""
        order_data = data.copy()
        
        # Convert ISO string dates back to datetime objects
        if "order_start" in order_data and isinstance(order_data["order_start"], str):
            order_data["order_start"] = datetime.fromisoformat(order_data["order_start"])
        if "order_completed" in order_data and isinstance(order_data["order_completed"], str):
            order_data["order_completed"] = datetime.fromisoformat(order_data["order_completed"])
        
        if items:
            order_data["order_items"] = items
        else:
            order_data["order_items"] = []
            
        return cls(**order_data)