import paho.mqtt.client as mqtt
import json
import config
from robot_otp import OTPVerifier
from robot_door import DoorController

class RobotController:
    def __init__(self):
        self.mqtt_options = config.mqtt_options
        self.robot_id = config.robot_id
        
        # Initialize components
        self.otp_verifier = OTPVerifier()
        self.door_controller = DoorController()
        
        # Set up door control callback
        self.otp_verifier.set_door_callback(self.door_controller.control)
        
        # Set up MQTT client
        self.client = mqtt.Client(client_id=self.mqtt_options['clientId'])
        self.client.username_pw_set(self.mqtt_options['username'], 
                                  self.mqtt_options['password'])
        self.client.tls_set()
        self.client.tls_insecure_set(False)
        
        # Set up MQTT callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to HiveMQ Cloud")
            self.client.subscribe(f"robot/{self.robot_id}/command")
        else:
            print("Failed to connect, return code %d\n", rc)

    def on_message(self, client, userdata, msg):
        try:
            message = json.loads(msg.payload)
            print("Received message:", message)
            if message['action'] == 'start_delivery':
               print('Received start_delivery command')
               print(message)
               owner_location = message['ownerLocation']
            # 1. Navigate to security guard's location
            # 2. Open the robot door
            # 3. Navigate to owner's location
            # 4. Send arrival notification
               arrival_message = {
                'deliveryId': message['deliveryId'],
                'message': 'I have arrived'
               }
               client.publish(f"robot/{robot_id}/arrival", json.dumps(arrival_message))
            # 5. Wait for owner to open the door
            # 6. Deliver the package
            elif message['action'] == 'set_otp':
                self.otp_verifier.set_otp(message['otp'], message['deliveryId'])
                print("otp")
            elif message['action'] == 'open_door':
                if self.otp_verifier.verify_delivery_id(message['deliveryId']):
                    self.door_controller.control("open")
                    print("opendoor")
            elif message['action'] == 'go_to_base':
                 print('Received go_to_base command')
                 base_location = message['baseLocation']
        except Exception as e:
            print(f"Error processing message: {e}")

    def start(self):
        """Start the robot controller"""
        try:
            self.client.connect(
                self.mqtt_options['broker'],
                self.mqtt_options['port'],
                self.mqtt_options['keepalive']
            )
            print("Starting MQTT loop...")
            self.client.loop_forever()
        except Exception as e:
            print(f"Error starting robot controller: {e}")

if __name__ == "__main__":
    controller = RobotController()
    controller.start()
