import json
import logging
import time
import paho.mqtt.client as mqtt
import psycopg2

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("direct_ingestor")

# Updated explicitly to match the real target DB environment discovered during docker inspect
DB_PARAMS = {
    "host": "127.0.0.1",
    "port": 5432,
    "database": "iob",
    "user": "postgres",
    "password": "postgres"
}

def insert_telemetry(data):
    conn = None
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        
        # We target industrial.telemetry table which is stored inside the 'iob' database
        query = """
            INSERT INTO industrial.telemetry (
                timestamp, machine_id, sensor_id, measured_value, 
                quality_code, alarm_status, sequence_number, metadata_fields
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """
        
        machine_id = data.get("machine_id", "UNKNOWN")
        sensor_id = data.get("sensor_id", "UNKNOWN")
        measured_value = data.get("value", 0.0)
        
        quality_str = str(data.get("quality", "GOOD")).upper()
        quality_code = 100 if quality_str == "GOOD" else 0

        cur.execute(query, (
            data.get("timestamp"),
            machine_id,
            sensor_id,
            float(measured_value),
            quality_code,
            data.get("alarm_status") or "NORMAL",
            int(data.get("sequence_number", 0)),
            json.dumps(data.get("metadata", {}))
        ))
        
        conn.commit()
        cur.close()
        logger.info(f"? [DATABASE SUCCESS] Saved Metric -> Machine: {machine_id} | Sensor: {sensor_id} | Value: {measured_value}")
    except Exception as e:
        logger.error(f"? [DATABASE ERROR] Insert rejected: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def on_connect(client, userdata, flags, rc, properties=None):
    logger.info("Ingestion pipeline successfully online and capturing live metrics!")
    client.subscribe("#") 

def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload_str = msg.payload.decode("utf-8")
        if "telemetry" in topic.lower():
            data = json.loads(payload_str)
            data["topic"] = topic
            insert_telemetry(data)
    except Exception as e:
        pass

def main():
    logger.info("Starting Corrected Ingestion Engine...")
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id="final_aligned_bridge")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("127.0.0.1", 1883, 60)
    client.loop_forever()

if __name__ == '__main__':
    main()
