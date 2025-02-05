from pydantic import BaseModel
from typing import List


class AnalogValues(BaseModel):
    values: List[float]
