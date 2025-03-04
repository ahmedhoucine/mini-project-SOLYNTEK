from pydantic import BaseModel
from typing import List

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    category: str
    is_favorite: bool = False

class ProductResponse(ProductCreate):
    id: int
    owner_username: str
    image_url: str

class UserCreate(BaseModel):
    username: str
    password: str
