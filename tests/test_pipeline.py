import json
import queue
import time
from ingestion.dispatcher import EventDispatcher
from ingestion.interfaces import InMemoryDatabaseWriter
from ingestion.models import RawTelemetryMessage
from ingestion.pipeline import TelemetryProcessingPipeline


def test_pipeline_end_to_end_sync():
    writer = InMemoryDatabaseWriter()
    pipeline = TelemetryProcessingPipeline()
    dispatcher = pipeline.get_dispatcher()
    if dispatcher:
        dispatcher.register_writer(writer)

    now = time.time()
    payload_dict = {
        "message_id": "pipeline-msg-001",
        "asset_id": "turbine-01",
        "timestamp": now,
        "topic": "site1/area1/line1/turbine-01/telemetry",
        "readings": {
            "temperature": {"value": 212.0, "unit": "F"},
            "vibration": {"value": 2.5, "unit": "in/s"}
        }
    }

    raw_msg = RawTelemetryMessage(
        topic="site1/area1/line1/turbine-01/telemetry",
        payload=json.dumps(payload_dict).encode("utf-8")
    )

    model = pipeline.process_raw_message(raw_msg)
    assert model is not None
    assert model.message_id == "pipeline-msg-001"
    assert model.asset_id == "turbine-01"
    # Verify normalization F -> CELSIUS (212F -> 100C)
    assert abs(model.measurements["temperature"].normalized_value - 100.0) < 0.001
    assert model.measurements["temperature"].normalized_unit == "CELSIUS"
    # Verify vibration in/s -> MM/S (2.5 * 25.4 = 63.5)
    assert abs(model.measurements["vibration"].normalized_value - 63.5) < 0.001
    # Verify DB writer received it
    assert len(writer.records) == 1
    assert writer.records[0].message_id == "pipeline-msg-001"


def test_pipeline_async_buffer_push():
    writer = InMemoryDatabaseWriter()
    buf_queue = queue.Queue()
    pipeline = TelemetryProcessingPipeline(buffer_queue=buf_queue, max_workers=2)
    dispatcher = pipeline.get_dispatcher()
    if dispatcher:
        dispatcher.register_writer(writer)

    pipeline.start()

    now = time.time()
    for i in range(5):
        raw = RawTelemetryMessage(
            topic=f"site1/area1/line1/turbine-01/telemetry",
            payload=json.dumps({
                "message_id": f"async-msg-{i}",
                "asset_id": "turbine-01",
                "timestamp": now,
                "readings": {"speed": 3000.0}
            })
        )
        buf_queue.put(raw)

    time.sleep(0.5)
    pipeline.stop()

    assert pipeline.processed_count == 5
    assert len(writer.records) == 5
