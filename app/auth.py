import os
import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from dotenv import load_dotenv

load_dotenv()

security = HTTPBearer()

# We need a separate variable for the JWT Secret
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """
    Verify JWT token from Supabase.
    Returns the decoded token payload if valid, raises HTTPException otherwise.
    """
    token = credentials.credentials
    
    try:
        # Debug logging
        print(f"Verifying token: {token[:10]}...")
        print(f"Using secret: {SUPABASE_JWT_SECRET[:5]}..." if SUPABASE_JWT_SECRET else "Secret is None!")
        
        # Decode and verify the JWT token
        # We disable audience verification to debug the "Invalid token" error
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False}
        )
        return payload
    except jwt.ExpiredSignatureError:
        print("Token verification failed: Expired signature")
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        print("Token verification failed: Invalid token")
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        print(f"Token verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
