from pydantic import BaseModel, Field
from typing import List, Optional

class MenuItemModel(BaseModel):
    food_name: str = Field(..., min_length=1)
    food_price: float = Field(..., gt=0)
    food_description: Optional[str] = None
    food_image: Optional[str] = None
    food_category: str
    
    
    def to_dict(self):
        """Convert model to dictionary for Firestore storage"""
        return self.model_dump(exclude_none=True)
        
    @classmethod
    def from_dict(cls, data: dict):
        """Create model instance from Firestore document"""
        return cls(**data)

class StallModel(BaseModel):
    stall_name: str = Field(..., min_length=1)
    stall_image: str = Field(..., min_length=1)
    stall_cover_image: Optional[str] = None
    stall_description: Optional[str] = None
    rating: float = Field(..., gt=0)
    review_count: int
    cuisines: Optional[List[str]]
    preparation_time_mins: int
    delivery_fee: float = Field(..., gt=0)
    stall_location: str = Field(..., min_length=1)
    is_promoted: bool
    menu: Optional[List[MenuItemModel]] = []
    
    def to_dict(self):
        """Convert model to dictionary for Firestore storage"""
        data = self.model_dump(exclude={"menu"}, exclude_none=True)
        return data
        
    @classmethod
    def from_dict(cls, data: dict, menu_items=None):
        """Create model instance from Firestore document and optional menu items"""
        stall_data = data.copy()
        if menu_items:
            stall_data["menu"] = menu_items
        return cls(**stall_data)