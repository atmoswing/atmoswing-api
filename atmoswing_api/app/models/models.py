from pydantic import BaseModel, AfterValidator
from typing import List, Optional, Annotated
from datetime import datetime


def round_to(ndigits: int, /) -> AfterValidator:
    return AfterValidator(lambda v: round(v, ndigits))


class Parameters(BaseModel):
    region: str
    forecast_date: Optional[datetime] = None
    target_date: Optional[datetime] = None
    lead_time: Optional[int] = None
    method: Optional[str] = None
    configuration: Optional[str] = None
    entity_id: Optional[int] = None
    percentile: Optional[int] = None
    percentiles: Optional[List[int]] = None
    number: Optional[int] = None
    normalize: Optional[int] = None


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
    criteria: List[Annotated[float, round_to(2)]]


class EntitiesValuesPercentileResponse(BaseModel):
    parameters: Parameters
    entity_ids: List[int]
    values: List[Annotated[float, round_to(2)]]
    values_normalized: List[Annotated[float, round_to(2)]]


class EntitiesValuesPercentileAggregationResponse(BaseModel):
    parameters: Parameters
    entity_ids: List[int]
    values: List[Annotated[float, round_to(2)]]
    values_normalized: List[Annotated[float, round_to(2)]]


class ReferenceValuesResponse(BaseModel):
    parameters: Parameters
    reference_axis: List[Annotated[float, round_to(2)]]
    reference_values: List[Annotated[float, round_to(2)]]


class SeriesAnalogValuesResponse(BaseModel):
    parameters: Parameters
    target_dates: List[datetime]
    series_dates: List[List[datetime]]
    series_values: List[List[Annotated[float, round_to(2)]]]


class SeriesValuesPercentile(BaseModel):
    percentile: int
    series_values: List[Annotated[float, round_to(2)]]


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
    value: Annotated[float, round_to(2)]
    criteria: Annotated[float, round_to(2)]
    rank: int


class AnalogsResponse(BaseModel):
    parameters: Parameters
    analogs: List[Analog]


class AnalogValuesResponse(BaseModel):
    parameters: Parameters
    values: List[Annotated[float, round_to(2)]]


class AnalogValuesPercentilesResponse(BaseModel):
    parameters: Parameters
    percentiles: List[int]
    values: List[Annotated[float, round_to(2)]]


class SeriesSynthesisPerMethod(BaseModel):
    method_id: str
    target_dates: List[datetime]
    values: List[Annotated[float, round_to(2)]]
    values_normalized: List[Annotated[float, round_to(2)]]


class SeriesSynthesisPerMethodListResponse(BaseModel):
    parameters: Parameters
    series_percentiles: List[SeriesSynthesisPerMethod]


class SeriesSynthesisTotal(BaseModel):
    time_step: int
    target_dates: List[datetime]
    values: List[Annotated[float, round_to(2)]]
    values_normalized: List[Annotated[float, round_to(2)]]


class SeriesSynthesisTotalListResponse(BaseModel):
    parameters: Parameters
    series_percentiles: List[SeriesSynthesisTotal]
