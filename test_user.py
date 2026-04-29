from app.database import SessionLocal
from app.services.user_service import create_user
from app.schemas.user_schema import UserCreate

db = SessionLocal()

user = create_user(
    db,
    UserCreate(
        email="teste@jadix.com",
        full_name="User Teste"
    )
)

print(user.id, user.email)