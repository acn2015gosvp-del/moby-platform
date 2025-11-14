import paho.mqtt.client as mqtt
from core.config import settings

client = mqtt.Client()

def publish_message(topic: str, payload: dict):
    client.connect(settings.MQTT_HOST, settings.MQTT_PORT, 60)
    client.publish(topic, str(payload))
    client.disconnect()
