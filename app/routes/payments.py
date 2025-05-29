import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from dotenv import load_dotenv
import razorpay

load_dotenv()
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

router = APIRouter(prefix="/razorpay", tags=["Razorpay"])

# Initialize the Razorpay client
client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

class OrderCreateRequest(BaseModel):
    amount: int
    currency: Optional[str] = "INR"
    receipt: Optional[str] = None
    notes: Optional[dict] = None

class OrderResponse(BaseModel):
    id: str
    entity: str
    amount: int
    currency: str
    receipt: Optional[str]
    status: str
    attempts: int
    created_at: int

class PlanCreateRequest(BaseModel):
    period: str  # "day", "week", "month", "year"
    interval: int
    item: dict = Field(..., description="Details of the plan item (name, amount, currency)")
    notes: Optional[dict] = None

class PlanResponse(BaseModel):
    id: str
    entity: str
    period: str
    interval: int
    item: dict
    status: str
    created_at: int

class SubscriptionCreateRequest(BaseModel):
    plan_id: str
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    start_at: Optional[int] = None
    quantity: Optional[int] = None
    notes: Optional[dict] = None

class SubscriptionResponse(BaseModel):
    id: str
    entity: str
    plan_id: str
    customer_id: Optional[str]
    status: str
    current_start: int
    current_end: int
    ended_at: Optional[int] = None
    quantity: int
    created_at: int

@router.post("/orders", response_model=OrderResponse)
async def create_razorpay_order(order_data: OrderCreateRequest):
    try:
        order = client.order.create(data=order_data.model_dump())
        return order
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/plans", response_model=PlanResponse)
async def create_razorpay_plan(plan_data: PlanCreateRequest):
    try:
        plan = client.plan.create(data=plan_data.model_dump())
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/subscriptions")
async def create_razorpay_subscription():
    try:
        subscription = client.subscription.create({
            "plan_id": "plan_QaSM4DlCxOYcXa",
            "customer_notify": 1,
            "quantity": 1,
            "total_count": 6,
        })

        print("Created Subscription:", subscription)

        # subscription = client.subscription.create(data=subscription_data.model_dump())
        return subscription
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))