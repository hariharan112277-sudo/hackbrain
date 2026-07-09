from ingestion.dispatcher import EventDispatcher
from ingestion.interfaces import InMemoryDatabaseWriter
from ingestion.models import ISA95HierarchyModel, TelemetryPayloadModel


def test_event_dispatcher_write():
    writer = InMemoryDatabaseWriter()
    dispatcher = EventDispatcher(writers=[writer])

    model = TelemetryPayloadModel(
        message_id="msg-100",
        asset_id="turbine-01",
        timestamp=1783000000.0,
        iso_timestamp="2026-07-02T10:00:00Z",
        isa95_hierarchy=ISA95HierarchyModel()
    )

    payload = {"_model": model}
    dispatcher.process(payload)

    assert len(writer.records) == 1
    assert writer.records[0].message_id == "msg-100"
