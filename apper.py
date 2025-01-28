from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from typing import List
from pymongo.errors import PyMongoError

# FastAPI initialization
app = FastAPI()

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
    email: str

# Home endpoint
@app.get("/")
def read_root():
    return {"message": "Claims Management System"}

# Create a new claim
@app.post("/claims", response_model=Claim)
def create_claim(claim: Claim):
    try:
        claim_dict = claim.dict()
        result = claims_collection.insert_one(claim_dict)
        claim_dict["_id"] = str(result.inserted_id)  # Convert ObjectId to string for return
        return claim_dict
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while creating the claim: {str(e)}")

# Get all claims
@app.get("/claims", response_model=List[Claim])
def get_claims():
    try:
        claims = claims_collection.find()
        claim_list = []
        for claim in claims:
            claim["_id"] = str(claim["_id"])  # Convert ObjectId to string for return
            claim_list.append(claim)
        return claim_list
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while retrieving claims: {str(e)}")

# Create a new user
@app.post("/users", response_model=User)
def create_user(user: User):
    try:
        user_dict = user.dict()
        result = users_collection.insert_one(user_dict)
        user_dict["_id"] = str(result.inserted_id)  # Convert ObjectId to string for return
        return user_dict
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while creating the user: {str(e)}")
