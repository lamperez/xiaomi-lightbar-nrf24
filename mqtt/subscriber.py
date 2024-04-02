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

    def on_connect(self, client, userdata, flags, rc, properties):
        print(f"Connected with result code {rc}")
        client.subscribe(self.topic)

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
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_forever()

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

# Usage
lightbar = Lightbar(ce_pin=25, csn_pin=0, remote_id=0xa2c231)
controller = MqttController("homeassistant.local", 1883,"mqtt_user", "password", "xiaomi/lightbar", lightbar)
controller.start()