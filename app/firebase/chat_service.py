from app.firebase.firebase_init import db
from google.cloud.firestore_v1 import ArrayUnion
from datetime import datetime
from typing import List, Dict

def get_user_chats(user_id: str) -> List[Dict]:
    chats_ref = db.collection("users").document(user_id).collection("chats")
    return [
        {"chat_id": chat.id, "createdAt": chat.to_dict().get("createdAt")}
        for chat in chats_ref.stream()
    ]

def create_chat(user_id: str, chat_id: str, message: dict):
    chat_ref = db.collection("users").document(user_id).collection("chats").document(chat_id)
    chat_ref.set({
        "createdAt": datetime.utcnow().isoformat(),
        "messages": [message]
    })

def add_message(user_id: str, chat_id: str, prompt: str):
    print(f"➡️  Adding message for user: {user_id}, chat: {chat_id}")
    
    chat_ref = db.collection("users").document(user_id).collection("chats").document(chat_id)
    chat_doc = chat_ref.get()
    
    if not chat_doc.exists:
        print("📄 Chat does not exist. Creating new chat document...")
        chat_ref.set({
            "createdAt": datetime.utcnow().isoformat(),
            "messages": ArrayUnion([prompt])
        })
        print("✅ Chat document created with first message.")
    else:
        print("📝 Chat exists. Appending message with ArrayUnion...")
        chat_ref.update({
            "messages": ArrayUnion([prompt])
        })
        print("✅ Message added to existing chat.")

def update_latest_code(user_id: str, chat_id: str, code: str):
    print(f"➡️  Adding code for user: {user_id}, chat: {chat_id}")
    
    chat_ref = db.collection("users").document(user_id).collection("chats").document(chat_id)
    chat_doc = chat_ref.get()
    
    if not chat_doc.exists:
        print("📄 Chat does not exist. Creating new chat document...")
        chat_ref.set({
            "createdAt": datetime.utcnow().isoformat(),
            "latest_code": [code]
        })
        print("✅ Chat document created with first code.")
    else:
        print("📝 Chat exists. Appending code with ArrayUnion...")
        chat_ref.update({
            "latest_code": [code]
        })
        print("✅ code added to existing chat.")

def get_chat_messages(user_id: str, chat_id: str):
    chat_doc = db.collection("users").document(user_id).collection("chats").document(chat_id).get()
    return chat_doc.to_dict() if chat_doc.exists else None

def get_latest_code(user_id: str):
    user_ref = db.collection("users").document(user_id).get()
    return user_ref.to_dict().get("latestCode", "")
