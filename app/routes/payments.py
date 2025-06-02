import hashlib
import hmac
import json
import os
from fastapi import APIRouter, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from dotenv import load_dotenv
import razorpay

from app.firebase.payment_service import PaymentDetails, add_payment_details, check_for_active_subscriptions, find_user_by_razorpay_customer_id

load_dotenv()
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")

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
    
class SubscriptionPayload(BaseModel):
    user_id: str

@router.post("/subscriptions")
def create_razorpay_subscription(req: SubscriptionPayload):
    try:
        res = check_for_active_subscriptions(req.user_id)

        if not res:
            subscription = client.subscription.create({
                "plan_id": "plan_QaSM4DlCxOYcXa",
                "customer_notify": 1,
                "quantity": 1,
                "total_count": 6,
            })

            print("Created Subscription:", subscription)
            return subscription
        else: 
            return {"message" : "User is already subscribed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

class VerifySubscriptionRequest(BaseModel):
    razorpay_payment_id: Optional[str] = None
    razorpay_subscription_id: str
    razorpay_signature: str
    user_id: str

def verify_signature(razorpay_payment_id, subscription_id, razorpay_signature, secret):
    message = f"{razorpay_payment_id}|{subscription_id}".encode('utf-8')
    key = secret.encode('utf-8')
    generated_signature = hmac.new(key, message, hashlib.sha256).hexdigest()

    if generated_signature == razorpay_signature:
        print("Payment is successful")
        return True
    else:
        print("Payment verification failed")
        return False

@router.post("/verify-subscription")
async def verify_razorpay_subscription(verification_data: VerifySubscriptionRequest):
    try:
        attributes = {
            'razorpay_subscription_id': verification_data.razorpay_subscription_id,
            'razorpay_payment_id': verification_data.razorpay_payment_id,
            'razorpay_signature': verification_data.razorpay_signature
        }

        res = verify_signature(attributes["razorpay_payment_id"], attributes["razorpay_subscription_id"], attributes["razorpay_signature"], RAZORPAY_KEY_SECRET)

        if res: 
            print("Payment signature verified successfully (using Razorpay SDK)")

            # Update Firebase database here to mark the subscription as active
            subscription_details = client.subscription.fetch(attributes["razorpay_subscription_id"])

            print("Subscription Details:", subscription_details)

            payment_info = PaymentDetails(
                razorpay_subscription_id=verification_data.razorpay_subscription_id,
                razorpay_payment_id=verification_data.razorpay_payment_id,
                status=subscription_details['status'],
                start_date=str(subscription_details['current_start']),
                end_date=str(subscription_details['current_end']),
                plan_id=subscription_details['plan_id']
            )

            add_payment_details(verification_data.user_id, payment_info, subscription_details['customer_id'])

            print("Subscription Details:", subscription_details)
            return {"status": "success", "message": "Subscription verified"}
        else: 
            raise HTTPException(status_code=400, detail="Invalid payment signature")

    except Exception as e:
        print(f"Error during verification: {e}")
        raise HTTPException(status_code=400, detail="Invalid payment signature")
    
@router.post("/webhook")
async def razorpay_webhook_handler(request: Request):
    body = await request.body()
    try:
        event = json.loads(body.decode('utf-8'))
        print("Webhook Request Body (JSON):", event)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    if not RAZORPAY_WEBHOOK_SECRET:
        print("RAZORPAY_WEBHOOK_SECRET environment variable not set!")
        return JSONResponse({"status": "error", "message": "Webhook secret not configured"}, status_code=500)
    
    razorpay_signature = request.headers.get("X-razorpay-signature")

    if razorpay_signature:
        try:
            print("signature: ", razorpay_signature)
            hmac_generated = hmac.new(
                RAZORPAY_WEBHOOK_SECRET.encode('utf-8'),
                body,
                hashlib.sha256
            ).hexdigest()

            if hmac_generated != razorpay_signature:
                print("Webhook signature verification failed.")
                return JSONResponse({"status": "error", "message": "Invalid webhook signature"}, status_code=400)
            else:
                print("Webhook signature verified successfully.")
                await process_webhook_event(event)
                return JSONResponse({"status": "success"})

        except Exception as e:
            print(f"Error verifying webhook signature: {e}")
            return JSONResponse({"status": "error", "message": "Error verifying signature"}, status_code=500)
    else:
        print("Razorpay-Signature header missing!")
        return JSONResponse({"status": "error", "message": "Missing signature header"}, status_code=400)

async def process_webhook_event(event: dict):
    event_type = event.get("event")
    payload = event.get("payload")

    print(f"Received webhook event: {event_type}") # Log all events

    customer_id = payload['subscription']['entity']['customer_id']
    subscription_id = payload['subscription']['entity']['id']
    status = payload['subscription']['entity']['status']
    plan_id = payload['subscription']['entity']['plan_id']
    start = payload['subscription']['entity']['current_start']
    end = payload['subscription']['entity']['current_end']

    user_id, user_data = find_user_by_razorpay_customer_id(customer_id)
    if user_id:
        print(f"Found user with ID: {user_id}")

        payment_info = PaymentDetails(
            razorpay_subscription_id=subscription_id,
            status=status,
            start_date=start,
            end_date=end,
            plan_id=plan_id
        )

        add_payment_details(user_id, payment_info, customer_id)
    else:
        print(f"No user found with Razorpay customer ID: {customer_id}")
