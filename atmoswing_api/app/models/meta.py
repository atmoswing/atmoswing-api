from pydantic import BaseModel
from typing import List
from typing import Optional

class Method(BaseModel):
    id: str
    name: str

class Configuration(BaseModel):
    id: str
    name: str

class MethodConfig(BaseModel):
    id: str
    name: str
    configurations: List[Configuration]

class Entity(BaseModel):
    id: int
    name: str
    x: float
    y: float
    official_id: Optional[str] = None
