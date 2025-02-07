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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection setup
client = MongoClient("mongodb://localhost:27017/")
db = client.claims_db
claims_collection = db.claims
users_collection = db.users
policies_collection = db.policies

# ==============================
# 🚀 Pydantic Models for Validation
# ==============================
class Claim(BaseModel):
    description: str
    status: str
    amount: float  # Add claim amount
    policyNumber: str  # Link claim to a policy

class User(BaseModel):
    id: str  # Add 'id' field
    name: str
    email: EmailStr

class Policy(BaseModel):
    policyNumber: str
    policyType: str
    amount: float  # Policy amount

# ==============================
# 🚀 Duplicate Check Functions
# ==============================
def is_duplicate_claim(description: str) -> bool:
    return claims_collection.find_one({"description": description}) is not None

def is_duplicate_user(email: str) -> bool:
    return users_collection.find_one({"email": email}) is not None

def is_duplicate_policy(policyNumber: str) -> bool:
    return policies_collection.find_one({"policyNumber": policyNumber}) is not None

# ==============================
# 🚀 CRUD for Claims
# ==============================
@app.post("/claims", response_model=Claim)
def create_claim(claim: Claim):
    try:
        if is_duplicate_claim(claim.description):
            raise HTTPException(status_code=400, detail="Claim with the same description already exists.")

        policy = policies_collection.find_one({"policyNumber": claim.policyNumber})
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found.")
        
        if claim.amount > policy["amount"]:
            raise HTTPException(status_code=400, detail="Claim amount exceeds policy amount.")
        
        claim_dict = claim.dict()
        result = claims_collection.insert_one(claim_dict)
        claim_dict["_id"] = str(result.inserted_id)
        return claim_dict
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Error creating claim: {str(e)}")

@app.get("/claims", response_model=List[Claim])
def get_claims():
    try:
        claims = claims_collection.find()
        return [{"_id": str(claim["_id"]), **claim} for claim in claims]
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving claims: {str(e)}")

# ==============================
# 🚀 CRUD for Users
# ==============================
@app.post("/users", response_model=User)
def create_user(user: User):
    try:
        if is_duplicate_user(user.email):
            raise HTTPException(status_code=400, detail="User with the same email already exists.")
        
        user_dict = user.dict()
        result = users_collection.insert_one(user_dict)
        user_dict["_id"] = str(result.inserted_id)
        return user_dict
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@app.get("/users", response_model=List[User])
def get_users():
    try:
        users = users_collection.find()
        return [{"_id": str(user["_id"]), **user} for user in users]
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving users: {str(e)}")

# ==============================
# 🚀 CRUD for Policies
# ==============================
@app.post("/policies")
def create_policy(policy: Policy):
    try:
        if is_duplicate_policy(policy.policyNumber):
            raise HTTPException(status_code=400, detail="Policy with this number already exists.")

        if policy.amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than zero.")
        
        policy_dict = policy.dict()
        result = policies_collection.insert_one(policy_dict)
        policy_dict["_id"] = str(result.inserted_id)
        return policy_dict
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Error creating policy: {str(e)}")

# ==============================
# 🚀 Prometheus Monitoring
# ==============================
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)
start_http_server(8000)

# ==============================
# 🚀 Root Endpoint
# ==============================
@app.get("/")
def read_root():
    return {"message": "Claims Management System"}



