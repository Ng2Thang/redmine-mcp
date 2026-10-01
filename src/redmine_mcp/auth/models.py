from dataclasses import dataclass, field


@dataclass(frozen=True)
class Principal:
    redmine_user_id: int


@dataclass(frozen=True)
class AuthContext:
    principal: Principal
    api_key: str = field(repr=False)
