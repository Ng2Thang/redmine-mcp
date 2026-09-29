from pydantic import BaseModel


class Reference(BaseModel):
    id: int
    name: str


class Project(BaseModel):
    id: int
    identifier: str
    name: str
    description: str | None = None
    status: int
    parent: Reference | None = None
