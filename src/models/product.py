"""Product models"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    """Base product model"""

    name: str = Field(..., min_length=1, max_length=255)
    sku: str = Field(..., min_length=1, max_length=100)
    location_id: str
    current_stock: int = Field(..., ge=0)
    max_stock: int = Field(..., gt=0)
    min_stock: int = Field(..., ge=0)
    reorder_point: int = Field(..., ge=0)
    unit_cost: Optional[float] = Field(None, ge=0)
    category: Optional[str] = None


class ProductCreate(ProductBase):
    """Product creation model"""

    pass


class ProductUpdate(BaseModel):
    """Product update model"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    current_stock: Optional[int] = Field(None, ge=0)
    max_stock: Optional[int] = Field(None, gt=0)
    min_stock: Optional[int] = Field(None, ge=0)
    reorder_point: Optional[int] = Field(None, ge=0)
    unit_cost: Optional[float] = Field(None, ge=0)
    category: Optional[str] = None


class Product(ProductBase):
    """Product model with metadata"""

    id: str
    velocity: Optional[float] = None  # Units sold per day
    days_until_stockout: Optional[int] = None
    suggested_reorder_quantity: Optional[int] = None
    last_updated: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class StockLevel(BaseModel):
    """Stock level summary"""

    product_id: str
    product_name: str
    sku: str
    location_id: str
    current_stock: int
    max_stock: int
    stock_percentage: float
    status: str  # "healthy", "low", "critical", "out_of_stock"
    velocity: Optional[float] = None
    days_until_stockout: Optional[int] = None
    suggested_reorder_quantity: Optional[int] = None
