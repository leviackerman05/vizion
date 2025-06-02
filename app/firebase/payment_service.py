from typing import Optional
from pydantic import BaseModel
from app.firebase.firebase_init import db
from firebase_admin import firestore
from google.cloud.exceptions import NotFound

class PaymentDetails(BaseModel):
    razorpay_payment_id: Optional[str] = None
    razorpay_subscription_id: str
    status: str
    start_date: str
    end_date: str
    plan_id: str

def add_payment_details(user_id: str, payment_details: PaymentDetails, customer_id: str):
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()

    if not user_doc.exists:
        print(f"User with ID {user_id} not found.")
        return

    update_data = {
        "customer_id": customer_id,
        "payments": payment_details.model_dump(exclude_unset=True)
    }

    try:
        user_ref.update(update_data)
        print(f"Payment details updated for user {user_id}.")
    except NotFound:
        print(f"Error: No document to update with ID {user_id}")
    except Exception as e:
        print(f"An error occurred during update: {e}")

def find_user_by_razorpay_customer_id(customer_id: str):
    users_ref = db.collection('users')
    query = users_ref.where(filter=firestore.FieldFilter('customer_id', '==', customer_id)).limit(1)
    results = query.stream()
    for doc in results:
        return doc.id, doc.to_dict()
    return None, None

def check_for_active_subscriptions(user_id: str) -> bool:
    user_ref = db.collection('users').document(user_id)
    user_doc = user_ref.get()

    if user_doc.exists:
        user_data = user_doc.to_dict()
        payments = user_data.get("payments")
        if payments and isinstance(payments, dict):
            status = payments.get("status")
            if status == "active":
                return True  # Found an active subscription
    return False  # No active subscription found or user doesn't exist

def get_active_plan_id(user_id: str) -> Optional[str]:
    user_ref = db.collection('users').document(user_id)
    user_doc = user_ref.get()

    if user_doc.exists:
        user_data = user_doc.to_dict()
        payments = user_data.get("payments")
        if payments and isinstance(payments, dict):
            plan_id = payments.get("plan_id")
            status = payments.get("status")
            if status == "active":
                return plan_id
    return None 