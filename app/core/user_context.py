from dataclasses import dataclass


@dataclass
class CurrentUser:
    id: int
    email: str | None = None
    is_admin: bool = False
    is_active: bool = True


def build_mock_current_user() -> CurrentUser:
    return CurrentUser(
        id=1,
        email="teste@jadix.com",
        is_admin=True,
        is_active=True,
    )