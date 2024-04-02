import paho.mqtt.client as mqtt
from xiaomi_lightbar import Lightbar

class MqttController:
    def __init__(self, broker, port, username, password, topic, lightbar):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.username_pw_set(username, password)
        self.broker = broker
        self.port = port
        self.topic = topic + "/#"
        self.lightbar = lightbar
        self.previous_control_state = ""

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
            print("Failed to connect, return code %d\n", rc)
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

# Constants for magic numbers and strings
CE_PIN = 25
CSN_PIN = 0
REMOTE_ID = 0xa2c231
BROKER = "homeassistant.local"
PORT = 1883
USERNAME = "mqtt_user"
PASSWORD = "password"
TOPIC = "xiaomi/lightbar"

# Create Lightbar and MqttController instances
lightbar = Lightbar(ce_pin=CE_PIN, csn_pin=CSN_PIN, remote_id=REMOTE_ID)

try:
    with MqttController(BROKER, PORT, USERNAME, PASSWORD, TOPIC, lightbar) as controller:
        controller.start()
        while True:  # Keep the program running
            pass
except KeyboardInterrupt:
    print("Interrupted by user. Exiting...")