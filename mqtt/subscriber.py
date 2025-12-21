import paho.mqtt.client as mqtt
from xiaomi_lightbar import Lightbar
import argparse
import time

description = """
    MQTT subscriber for Xiaomi Lightbar Home Assistant MQTT Light integration.
    This script subscribes to the MQTT topic and controls the Xiaomi Lightbar based on the received messages by using the xiaomi_lightbar library.
"""

parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawDescriptionHelpFormatter)

parser.add_argument("--broker", type=str, default="homeassistant.local", help="MQTT Broker")
parser.add_argument("--port", type=int, default=1883, help="MQTT Port")
parser.add_argument("--username", type=str, default="", help="MQTT Username")
parser.add_argument("--password", type=str, default="", help="MQTT Password")
parser.add_argument("--topic", type=str, default="xiaomi/lightbar", help="MQTT Topic")
parser.add_argument("--ce_pin", type=int, default=25, help="CE Pin")
parser.add_argument("--csn_pin", type=int, default=0, help="CSN Pin")
parser.add_argument("--remote_id", type=lambda x: int(x, 16), default=0xABCDEF, help="Remote ID")

args = parser.parse_args()

CE_PIN = args.ce_pin
CSN_PIN = args.csn_pin
REMOTE_ID = args.remote_id
BROKER = args.broker
PORT = args.port
USERNAME = args.username
PASSWORD = args.password
TOPIC = args.topic

# Create Lightbar and MqttController instances
lightbar = Lightbar(ce_pin=CE_PIN, csn_pin=CSN_PIN, remote_id=REMOTE_ID)

class MqttController:
    def __init__(self, broker, port, username, password, topic, lightbar):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if username != "":
            self.client.username_pw_set(username, password)
        self.broker = broker
        self.port = port
        self.topic = topic + "/#"
        self.lightbar = lightbar
        # Store the previous control state to avoid sending the same on_off command multiple times
        # we assume the default state to be ON
        self.previous_control_state = "ON"

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def on_connect(self, client, userdata, flags, rc, properties):
        if rc == 0:
            print("Connected to MQTT Broker!")
            client.subscribe(self.topic)
        else:
            print(f"Failed to connect, return code: {rc}")
            self.stop()

    def on_message(self, client, userdata, msg):
        print(f"{msg.topic} {msg.payload}")
        if msg.topic == self.topic.replace("#", "control"):
            if msg.payload == b"ON":
                if self.previous_control_state != "ON":
                    self.lightbar.on_off()
                    self.previous_control_state = "ON"
            if msg.payload == b"OFF":
                if self.previous_control_state != "OFF":
                    self.lightbar.on_off()
                    self.previous_control_state = "OFF"

        elif msg.topic == self.topic.replace("#", "brightness/set"):
            val = int(msg.payload)
            scaled_val = round((val / 255) * 15)
            print(f"Brightness: {scaled_val}")
            self.lightbar.brightness(scaled_val)
        elif msg.topic == self.topic.replace("#", "temperature/set"):
            val = int(msg.payload)
            scaled_val = scale_value(val)
            print(f"temperature: {scaled_val}")
            self.lightbar.color_temp(scaled_val)

    def start(self):
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
        except Exception as e:
            print(f"Failed to connect to MQTT broker: {e}")

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

def scale_value(t):
    if 153 <= t <= 219:
        a1, b1 = 153, 219
        c1, d1 = 15, 7
        f_t = c1 + (d1 - c1) * ((t - a1) / (b1 - a1))
    elif 219 < t <= 370:
        a2, b2 = 219, 370
        c2, d2 = 7, 0
        f_t = c2 + (d2 - c2) * ((t - a2) / (b2 - a2))
    else:
        f_t = None
    return round(f_t) if f_t is not None else None

def main():
    try:
        with MqttController(BROKER, PORT, USERNAME, PASSWORD, TOPIC, lightbar) as controller:
            controller.start()
            while True:  # Keep the program running
                time.sleep(0.1)
                pass
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting...")

if __name__ == "__main__":
    main()
