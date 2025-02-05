from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient
from typing import List
from pymongo.errors import PyMongoError
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import start_http_server

# FastAPI initialization
app = FastAPI()

# Add CORS middleware here
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (you can restrict to specific domains in production)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# MongoDB connection setup
client = MongoClient("mongodb://localhost:27017/claim_management")  # Adjust if using MongoDB Atlas or different URL
db = client.claims_db  # Select the database
claims_collection = db.claims  # Select the 'claims' collection
users_collection = db.users  # Select the 'users' collection

# Pydantic models for data validation
class Claim(BaseModel):
    description: str
    status: str

class User(BaseModel):
    name: str
    email: EmailStr  # Ensures valid email format

# Home endpoint
@app.get("/")
def read_root():
    return {"message": "Claims Management System"}

# Check for duplicate claim by description
def is_duplicate_claim(description: str) -> bool:
    return claims_collection.find_one({"description": description}) is not None

# Check for duplicate user by email
def is_duplicate_user(email: str) -> bool:
    return users_collection.find_one({"email": email}) is not None

# Create a new claim with custom error handling and duplicate check
@app.post("/claims", response_model=Claim)
def create_claim(claim: Claim):
    try:
        # Check for duplicate claim
        if is_duplicate_claim(claim.description):
            raise HTTPException(status_code=400, detail="Claim with the same description already exists.")
        
        # If no duplicate, insert the claim into the database
        claim_dict = claim.dict()
        result = claims_collection.insert_one(claim_dict)
        claim_dict["_id"] = str(result.inserted_id)  # Convert ObjectId to string for return
        return claim_dict
    except PyMongoError as e:
        # Custom MongoDB error handling
        raise HTTPException(status_code=500, detail=f"An error occurred while creating the claim: {str(e)}")

# Get all claims with custom error handling
@app.get("/claims", response_model=List[Claim])
def get_claims():
    try:
        claims = claims_collection.find()
        claim_list = []
        for claim in claims:
            # Ensure 'description' and 'status' exist, add default if missing
            if 'description' not in claim or 'status' not in claim:
                continue  # Skip claims that do not have required fields

            claim["_id"] = str(claim["_id"])  # Convert ObjectId to string for return
            claim_list.append(claim)
        return claim_list
    except PyMongoError as e:
        # Custom MongoDB error handling
        raise HTTPException(status_code=500, detail=f"An error occurred while retrieving claims: {str(e)}")

# Create a new user with custom error handling and duplicate check
@app.post("/users", response_model=User)
def create_user(user: User):
    try:
        # Check for duplicate user
        if is_duplicate_user(user.email):
            raise HTTPException(status_code=400, detail="User with the same email already exists.")
        
        # If no duplicate, insert the user into the database
        user_dict = user.dict()
        result = users_collection.insert_one(user_dict)
        user_dict["_id"] = str(result.inserted_id)  # Convert ObjectId to string for return
        return user_dict
    except PyMongoError as e:
        # Custom MongoDB error handling
        raise HTTPException(status_code=500, detail=f"An error occurred while creating the user: {str(e)}")

# Get all users with custom error handling
@app.get("/users", response_model=List[User])
def get_users():
    try:
        users = users_collection.find()
        user_list = []
        for user in users:
            user["_id"] = str(user["_id"])  # Convert ObjectId to string for return
            user_list.append(user)
        return user_list
    except PyMongoError as e:
        # Custom MongoDB error handling
        raise HTTPException(status_code=500, detail=f"An error occurred while retrieving users: {str(e)}")

# Prometheus Metrics Exporter
instrumentator = Instrumentator()

# This will automatically create a /metrics endpoint where Prometheus can scrape the metrics
instrumentator.instrument(app).expose(app)

# Run the Prometheus HTTP server on a different port for monitoring (optional)
start_http_server(8000)  # This runs Prometheus server on port 8000

