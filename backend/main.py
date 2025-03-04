import shutil
from uuid import uuid4
from fastapi import FastAPI, File, Request, UploadFile, Form, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from models import Product, User
from database import SessionLocal, engine
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os
import json
import redis
from celery import Celery
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


# OAuth2 configuration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# CORS middleware configuration
origins = [
    "http://localhost:3000",  # React frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis for caching
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Celery Configuration for background tasks
celery = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

# Dependency for database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT secret and algorithm
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# User schema
class UserCreate(BaseModel):
    username: str
    password: str

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user: UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    return "complete"

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# Exception handler for rate limit
@app.exception_handler(RateLimitExceeded)
def rate_limit_exceeded_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please try again later."}
    )

@app.post("/register")
@limiter.limit("5/minute")  # Limit to 5 requests per minute per IP
async def register_user(request: Request, user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return create_user(db=db, user=user)


# JWT Token creation
def authenticate_user(username: str, password: str, db: Session):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not pwd_context.verify(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.post("/token")
@limiter.limit("10/minute")  # Limit to 10 requests per minute per IP
def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# Product schemas
class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    category: str
    is_favorite: bool = False

class ProductResponse(ProductCreate):
    id: int
    owner_username: str
    image_url:  Optional[str] 

@app.get("/products", response_model=List[ProductResponse])
def get_products(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    # Decode the token and extract the username
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Caching logic with Redis
    cache_key = f"products_{username}"
    cached_products = redis_client.get(cache_key)

    if cached_products:
        return json.loads(cached_products)

    # Fetch from the database if not found in cache
    products = db.query(Product).filter(Product.owner_username == username).all()
    products_list = [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "category": p.category,
            "is_favorite": p.is_favorite,
            "owner_username": p.owner_username,
            "image_url": p.image_url,
        }
        for p in products
    ]

    # Cache the result for 5 minutes (300 seconds)
    redis_client.setex(cache_key, 300, json.dumps(products_list))

    return products

@app.post("/products", response_model=ProductResponse)
def create_product(
    product: str = Form(...),  # Receive JSON data as a string
    image: UploadFile = File(None),  # Image is optional
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    # Decode the JWT token
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Parse the incoming product data
    try:
        product_data = json.loads(product)
        product_obj = ProductCreate(**product_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid product data format")

    # Save image if uploaded
    image_url = None
    if image:
        image_path = os.path.join(UPLOAD_DIR, image.filename)
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        image_url = f"/uploads/{image.filename}"

    # Create product in database
    db_product = Product(owner_username=username, image_url=image_url, **product_obj.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    # Invalidate cache after adding new product
    redis_client.delete(f"products_{username}")

    return db_product

@app.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product: str = Form(...),  # Receive JSON data as a string
    image: UploadFile = File(None),  # Image is optional
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    # Decode the JWT token to get the username
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Fetch the existing product
    db_product = db.query(Product).filter(Product.id == product_id, Product.owner_username == username).first()
    if not db_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    # Parse the incoming product data
    try:
        product_data = json.loads(product)
        updated_product = ProductCreate(**product_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid product data format")

    # Update product fields
    db_product.name = updated_product.name
    db_product.description = updated_product.description
    db_product.price = updated_product.price
    db_product.category = updated_product.category
    db_product.is_favorite = updated_product.is_favorite

    # Update image if provided
    if image:
        image_path = os.path.join(UPLOAD_DIR, image.filename)
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        db_product.image_url = f"/uploads/{image.filename}"

    db.commit()
    db.refresh(db_product)

    # Invalidate cache after update
    redis_client.delete(f"products_{username}")

    return db_product

@app.patch("/products/{product_id}/favorite")
def update_favorite_status(
    product_id: int,
    is_favorite: bool = Form(...),  # Accepting boolean value
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    # Decode JWT token to get the username
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Fetch the existing product
    db_product = db.query(Product).filter(Product.id == product_id, Product.owner_username == username).first()
    if not db_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    # Update favorite status
    db_product.is_favorite = is_favorite
    db.commit()
    db.refresh(db_product)

    # Invalidate cache after update
    redis_client.delete(f"products_{username}")

    return {"message": "Favorite status updated", "product_id": product_id, "is_favorite": db_product.is_favorite}

@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product_by_id(product_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    # Decode the token and extract the username
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    cache_key = f"products_{username}"
    cached_products = redis_client.get(cache_key)

    if cached_products:
        products_list = json.loads(cached_products)
        product = next((p for p in products_list if p["id"] == product_id), None)
        if product:
            return product
    
    # Fetch the product by ID and check if it belongs to the current user
    product = db.query(Product).filter(Product.id == product_id, Product.owner_username == username).first()
    
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    return product

@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    product = db.query(Product).filter(Product.id == product_id, Product.owner_username == username).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()

    # Invalidate cache after deletion
    redis_client.delete(f"products_{username}")

    return {"message": "Product deleted"}

# Celery task for async processing
@celery.task
def long_running_task():
    import time
    time.sleep(10)  # Simulate a long-running task
    return "Task Completed"

@app.get("/start-task")
def start_task():
    task = long_running_task.apply_async()
    return {"task_id": task.id, "status": "Task Started"}

@app.get("/task-status/{task_id}")
def get_task_status(task_id: str):
    task_result = long_running_task.AsyncResult(task_id)
    return {"task_id": task_id, "status": task_result.status, "result": task_result.result}