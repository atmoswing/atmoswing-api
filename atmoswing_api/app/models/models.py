from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime


class Parameters(BaseModel):
    region: str
    forecast_date: Optional[datetime] = None
    target_date: Optional[datetime] = None
    method: Optional[str] = None
    configuration: Optional[str] = None
    entity_id: Optional[int] = None
    percentile: Optional[int] = None
    percentiles: Optional[List[int]] = None


class FloatValue(BaseModel):
    value: float

    @field_validator("value")
    def round_value(cls, v: float) -> float:
        return round(float(v), 2)


class FloatValues(BaseModel):
    values: List[float]

    @field_validator("values")
    def round_values(cls, v: List[float]) -> List[float]:
        return [round(float(value), 2) for value in v]


class Method(BaseModel):
    id: str
    name: str


class MethodsListResponse(BaseModel):
    parameters: Parameters
    methods: List[Method]


class Configuration(BaseModel):
    id: str
    name: str


class MethodConfig(BaseModel):
    id: str
    name: str
    configurations: List[Configuration]


class MethodConfigsListResponse(BaseModel):
    parameters: Parameters
    methods: List[MethodConfig]


class Entity(BaseModel):
    id: int
    name: str
    x: float
    y: float
    official_id: Optional[str] = None


class EntitiesListResponse(BaseModel):
    parameters: Parameters
    entities: List[Entity]


class AnalogDatesResponse(BaseModel):
    parameters: Parameters
    analog_dates: List[datetime]


class AnalogCriteriaResponse(BaseModel):
    parameters: Parameters
    criteria: FloatValues


class EntitiesValuesPercentileResponse(BaseModel):
    parameters: Parameters
    entity_ids: List[int]
    values: FloatValues


class ReferenceValuesResponse(BaseModel):
    parameters: Parameters
    axis: FloatValues
    values: FloatValues


class SeriesAnalogValuesResponse(BaseModel):
    parameters: Parameters
    series_values: List[FloatValue]


class SeriesValuesPercentile(BaseModel):
    percentile: int
    series_values: FloatValues


class SeriesValuesPercentiles(BaseModel):
    forecast_date: datetime
    target_dates: List[datetime]
    series_percentiles: List[SeriesValuesPercentile]


class SeriesValuesPercentilesResponse(BaseModel):
    parameters: Parameters
    series_values: SeriesValuesPercentiles


class SeriesValuesPercentilesHistoryResponse(BaseModel):
    parameters: Parameters
    past_forecasts: List[SeriesValuesPercentiles]


class Analog(BaseModel):
    date: datetime
    value: FloatValue
    criteria: FloatValue
    rank: int


class AnalogsResponse(BaseModel):
    parameters: Parameters
    analogs: List[Analog]


class AnalogValuesResponse(BaseModel):
    parameters: Parameters
    values: FloatValues


class AnalogValuesPercentilesResponse(BaseModel):
    parameters: Parameters
    percentiles: List[int]
    values: FloatValues


class SeriesSynthesisPerMethod(BaseModel):
    method_id: str
    target_dates: List[datetime]
    values: FloatValues


class SeriesSynthesisPerMethodListResponse(BaseModel):
    parameters: Parameters
    series_percentiles: List[SeriesSynthesisPerMethod]


class SeriesSynthesisTotal(BaseModel):
    time_step: int
    target_dates: List[datetime]
    values: FloatValues


class SeriesSynthesisTotalListResponse(BaseModel):
    parameters: Parameters
    series_percentiles: List[SeriesSynthesisTotal]
