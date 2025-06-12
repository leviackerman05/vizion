from typing import Optional
from pydantic import BaseModel
from app.firebase.firebase_init import db
from firebase_admin import firestore
from google.cloud.exceptions import NotFound

class PaymentDetails(BaseModel):
    customer_id:Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    razorpay_subscription_id: str
    status: str
    start_date: str
    end_date: str
    plan_id: str

def add_payment_details(user_id: str, payment_details: PaymentDetails):
    user_ref = db.collection("users").document(user_id)


    try:
        user_ref.update(payment_details.model_dump(exclude_unset=True))
        print(f"Payment details updated for user {user_id}.")
    except NotFound:
        print(f"Error: No document to update with ID {user_id}")
    except Exception as e:
        print(f"An error occurred during update: {e}")

def find_user_by_razorpay_subscription_id(subscription_id: str):
    users_ref = db.collection('users')
    query = users_ref.where(filter=firestore.FieldFilter('razorpay_subscription_id', '==', subscription_id)).limit(1)
    results = query.stream()
    for doc in results:
        return doc.id, doc.to_dict()
    return None, None

def check_for_active_subscriptions(user_id: str) -> bool:
    user_ref = db.collection('users').document(user_id)
    user_doc = user_ref.get()

    if user_doc.exists:
        user_data = user_doc.to_dict()
        status = user_data.get("status")
        if status and status == "active":
            return True 
    return False

def get_active_plan_id(user_id: str) -> Optional[str]:
    user_ref = db.collection('users').document(user_id)
    user_doc = user_ref.get()

    if user_doc.exists:
        user_data = user_doc.to_dict()
        plan_id = user_data.get("plan_id")
        status = user_data.get("status")
        if status and plan_id and status == "active":
            return plan_id
    return None 