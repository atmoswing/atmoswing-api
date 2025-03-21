from pydantic import BaseModel, field_validator
from typing import List
from datetime import datetime


class ReferenceValues(BaseModel):
    axis: List[float]
    values: List[float]

    @field_validator("axis")
    def round_axis(cls, v: List[float]) -> List[float]:
        return [round(float(value), 2) for value in v]

    @field_validator("values")
    def round_values(cls, v: List[float]) -> List[float]:
        return [round(float(value), 2) for value in v]


class Analog(BaseModel):
    date: datetime
    value: float
    criteria: float
    rank: int

    @field_validator("value")
    def round_value(cls, v: float) -> float:
        return round(float(v), 2)

    @field_validator("criteria")
    def round_criteria(cls, v: float) -> float:
        return round(float(v), 3)


class Analogs(BaseModel):
    analogs: List[Analog]


class AnalogValues(BaseModel):
    values: List[float]

    @field_validator("values")
    def round_values(cls, v: List[float]) -> List[float]:
        return [round(float(value), 2) for value in v]


class AnalogDates(BaseModel):
    dates: List[datetime]


class AnalogCriteria(BaseModel):
    criteria: List[float]

    @field_validator("criteria")
    def round_criteria(cls, v: List[float]) -> List[float]:
        return [round(float(value), 3) for value in v]


class SeriesAnalogValues(BaseModel):
    series_values: List[List[float]]

    @field_validator("series_values")
    def round_series(cls, v: List[List[float]]) -> List[List[float]]:
        return [[round(float(value), 2) for value in series] for series in v]


class SeriesAnalogValuesPercentile(BaseModel):
    percentile: int
    series_values: List[float]

    @field_validator("series_values")
    def round_series(cls, v: List[float]) -> List[float]:
        return [round(float(value), 2) for value in v]


class SeriesAnalogValuesPercentiles(BaseModel):
    series_percentiles: List[SeriesAnalogValuesPercentile]
