import json
import hashlib
import uuid
import subprocess
import paho.mqtt.client as mqtt

def generate_deterministic_uuid(text_string):
    if not text_string:
        text_string = "UNKNOWN"
    hex_digest = hashlib.md5(text_string.encode('utf-8')).hexdigest()
    return f"{hex_digest[:8]}-{hex_digest[8:12]}-{hex_digest[12:16]}-{hex_digest[16:20]}-{hex_digest[20:]}"

def on_connect(client, userdata, flags, rc, properties=None):
    print("?? Direct Streamer active! Writing metrics directly without validation gates...")
    client.subscribe("#")

def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        if "telemetry" in topic.lower():
            data = json.loads(msg.payload.decode("utf-8"))
            
            row_id = str(uuid.uuid4())
            machine_uuid = generate_deterministic_uuid(data.get("machine_id"))
            sensor_uuid = generate_deterministic_uuid(data.get("sensor_id"))
            
            measured_value = float(data.get("value", 0.0))
            timestamp = data.get("timestamp")
            quality = 100 if str(data.get("quality")).upper() == "GOOD" else 0
            alarm = data.get("alarm_status") or "NORMAL"
            seq = int(data.get("sequence_number", 0))
            metadata = json.dumps(data.get("metadata", {}))

            # Direct insert statement with no external dependencies
            sql = f"""
            INSERT INTO industrial.telemetry (
                id, timestamp, machine_id, sensor_id, measured_value, 
                quality_code, alarm_status, sequence_number, metadata_fields
            ) VALUES ('{row_id}', '{timestamp}', '{machine_uuid}', '{sensor_uuid}', {measured_value}, {quality}, '{alarm}', {seq}, '{metadata}');
            """
            
            cmd = ["docker", "exec", "-i", "iob_postgres_db", "psql", "-U", "postgres", "-d", "iob", "-c", sql]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"? [DATABASE INSERT SUCCESS] Saved -> Machine: {data.get('machine_id')} | Value: {measured_value}")
            else:
                print(f"? [INSERT REJECTED] {result.stderr.strip()}")
    except Exception as e:
        print(f"?? Execution anomaly observed: {e}")

def main():
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id="direct_unconstrained_streamer")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("127.0.0.1", 1883, 60)
    client.loop_forever()

if __name__ == '__main__':
    main()
