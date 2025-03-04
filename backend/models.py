from sqlalchemy import Column, Integer, String
from database import Base
from database import engine
from sqlalchemy.orm import relationship
from sqlalchemy import  Column, String, Float, Boolean, ForeignKey


# User model
class User(Base):
    __tablename__ = "users"

    username = Column(String,primary_key=True, unique=True, index=True)
    hashed_password = Column(String)
    products = relationship("Product", back_populates="owner")

# Product model
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Float)
    category = Column(String)
    is_favorite = Column(Boolean, default=False)
    image_url = Column(String)
    owner_username = Column(String, ForeignKey("users.username"))
    owner = relationship("User", back_populates="products")


User.metadata.create_all(bind=engine)
