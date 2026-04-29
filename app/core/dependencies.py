from fastapi import Header
from typing import Optional

from app.core.user_context import CurrentUser


def get_current_user(
    x_user_id: Optional[int] = Header(default=None),
) -> CurrentUser:
    """
    Simula usuário baseado em header.
    Se não vier header, usa usuário mock padrão (id=1)
    """

    user_id = x_user_id if x_user_id else 1

    return CurrentUser(
        id=user_id,
        email=f"user{user_id}@jadix.com",
        is_admin=True if user_id == 1 else False,
        is_active=True,
    )


def get_current_user_id(
    x_user_id: Optional[int] = Header(default=None),
) -> int:
    return x_user_id if x_user_id else 1