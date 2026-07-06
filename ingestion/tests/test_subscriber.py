import queue
from ingestion.models import RawTelemetryMessage
from ingestion.subscriber import MqttTelemetrySubscriber


def test_subscriber_push_to_buffer():
    buf = queue.Queue(maxsize=10)
    subscriber = MqttTelemetrySubscriber(buffer_queue=buf, client_id="test_sub")
    raw = RawTelemetryMessage(topic="site1/area1/line1/turbine-01/telemetry", payload=b'{"test": 1}')
    subscriber.push_to_buffer(raw)
    assert not buf.empty()
    item = buf.get()
    assert item.topic == "site1/area1/line1/turbine-01/telemetry"
