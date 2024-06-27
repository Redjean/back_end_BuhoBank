from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from models import CustomerModel 
from crud import add_customer
from fastapi.encoders import jsonable_encoder

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)


@app.post("/register_user", response_description="Add new customer", response_model=CustomerModel)
async def create_customer(customer: CustomerModel):
    new_customer = await add_customer(customer)
    if new_customer:
        new_customer = jsonable_encoder(new_customer)
        
    return JSONResponse(status_code=201, content=new_customer)
