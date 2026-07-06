"""
Historical Query Orchestrator Layer.
"""
import math
from typing import List, Any
from uuid import UUID
from datetime import datetime
from integration.interfaces import (
    IHistoricalQueryService, ITelemetryRepository, IAlarmRepository,
    IEventRepository, IMaintenanceRepository
)
from integration.contracts import (
    TelemetryDTO, MachineEventDTO, AlarmDTO, MaintenanceLogDTO,
    QueryCriteriaDTO, AggregatedStatisticsDTO
)
from integration.exceptions import InvalidQueryCriteriaException


class HistoricalQueryService(IHistoricalQueryService):
    def __init__(self, telemetry_repo: ITelemetryRepository, alarm_repo: IAlarmRepository,
                 event_repo: IEventRepository, maintenance_repo: IMaintenanceRepository):
        self._telemetry_repo = telemetry_repo
        self._alarm_repo = alarm_repo
        self._event_repo = event_repo
        self._maintenance_repo = maintenance_repo

    def get_historical_telemetry(self, session: Any, sensor_id: UUID, criteria: QueryCriteriaDTO) -> List[TelemetryDTO]:
        if criteria.start_time >= criteria.end_time:
            raise InvalidQueryCriteriaException("Chronological criteria boundaries are inverted; Start must precede End.")

        raw_data = self._telemetry_repo.get_time_range(session, sensor_id, criteria.start_time, criteria.end_time)
        return [TelemetryDTO.model_validate(r) for r in raw_data]

    def get_historical_events(self, session: Any, machine_id: UUID, criteria: QueryCriteriaDTO) -> List[MachineEventDTO]:
        raw_data = self._event_repo.get_historical_window(session, machine_id, criteria.start_time, criteria.end_time)
        return [MachineEventDTO.model_validate(r) for r in raw_data]

    def get_historical_alarms(self, session: Any, machine_id: UUID, criteria: QueryCriteriaDTO) -> List[AlarmDTO]:
        raw_data = self._alarm_repo.get_historical_window(session, machine_id, criteria.start_time, criteria.end_time)
        return [AlarmDTO.model_validate(r) for r in raw_data]

    def get_maintenance_history(self, session: Any, machine_id: UUID, criteria: QueryCriteriaDTO) -> List[MaintenanceLogDTO]:
        raw_data = self._maintenance_repo.get_historical_window(session, machine_id, criteria.start_time, criteria.end_time)
        return [MaintenanceLogDTO.model_validate(r) for r in raw_data]

    def get_aggregated_statistics(self, session: Any, sensor_id: UUID, start: datetime, end: datetime) -> AggregatedStatisticsDTO:
        raw_data = self._telemetry_repo.get_time_range(session, sensor_id, start, end)
        if not raw_data:
            return AggregatedStatisticsDTO(sensor_id=sensor_id, datapoint_count=0, minimum_value=0.0, maximum_value=0.0, mean_value=0.0, standard_deviation=0.0, variance=0.0)

        values = [r.measured_value for r in raw_data]
        n = len(values)
        min_v, max_v = min(values), max(values)
        mean_v = sum(values) / n
        var_v = sum((x - mean_v) ** 2 for x in values) / n if n > 1 else 0.0

        return AggregatedStatisticsDTO(
            sensor_id=sensor_id, datapoint_count=n, minimum_value=min_v, maximum_value=max_v,
            mean_value=mean_v, standard_deviation=math.sqrt(var_v), variance=var_v
        )
