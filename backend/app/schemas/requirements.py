# app/schemas/requirements.py

from pydantic import BaseModel

class Requirement(BaseModel):
    id: str
    title: str
    description: str

class Module(BaseModel):
    name: str
    requirements: list[Requirement]