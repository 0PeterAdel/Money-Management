# security.py
from passlib.context import CryptContext

# Setup the password hashing context using bcrypt, which is the standard and very secure.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password and returns the hash."""
    return pwd_context.hash(password)