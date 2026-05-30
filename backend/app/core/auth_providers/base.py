from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass
class AuthUser:
    id: UUID
    email: str


class AuthProvider(ABC):
    @abstractmethod
    async def register(self, email: str, password: str, display_name: str) -> AuthUser:
        ...

    @abstractmethod
    async def login(self, email: str, password: str) -> AuthUser:
        ...

    @abstractmethod
    async def verify_access_token(self, token: str) -> AuthUser:
        ...
