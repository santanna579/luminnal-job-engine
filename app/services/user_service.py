from sqlalchemy.orm import Session
from app.models_user import User
from app.schemas.user_schema import UserCreate

def create_user(db: Session, user_data: UserCreate):
    user = User(
        email=user_data.email,
        full_name=user_data.full_name
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()