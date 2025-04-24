import paho.mqtt.client as mqtt
import json
from PyQt5.QtCore import QObject, pyqtSignal

class MQTTClient(QObject):
    temperature_updated = pyqtSignal(int, float, float, float)  # tunnel_id, output_temp, external_temp, internal_temp
    defrost_status_updated = pyqtSignal(int, bool)  # tunnel_id, defrost_status
    tunnel_status_updated = pyqtSignal(int, bool)  # tunnel_id, running_status
    connection_status = pyqtSignal(bool)  # connected status
    error_occurred = pyqtSignal(str)  # error message
    
    def __init__(self):
        super().__init__()
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.client.on_subscribe = self.on_subscribe
        self.client.on_publish = self.on_publish
        self.reconnect_delay = 3  # seconds
        self.max_retries = 10
        self.retry_count = 0
        self.connected = False
        self.subscriptions = set()
        self.pending_subscriptions = set()
        # Default configuration
        self.config = {
            'broker': '172.25.2.52',
            'port': 1883,
            'topics': {
                'send': 'A_RECIBIR',
                'receive': 'A_ENVIAR'
            },
            'messages': {
                'start': 'start',
                'stop': 'stop'
            }
        }

    def on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback when subscription is confirmed"""
        print(f"Subscription confirmed with QoS: {granted_qos}")
        # Add successfully subscribed topics to subscriptions set
        for topic in self.pending_subscriptions.copy():
            self.subscriptions.add(topic)
            self.pending_subscriptions.remove(topic)
    
    def configure(self, config):
        """Update MQTT configuration"""
        self.config.update(config)
        # Store access code for future use
        self.access_code = config.get('access_code', 'migiva')
    
    def connect(self):
        """Connect to MQTT broker with retry mechanism"""
        self.retry_count = 0
        self._try_connect()

    def _try_connect(self):
        """Internal method to attempt connection with retry logic"""
        if self.retry_count >= self.max_retries:
            error_msg = "Maximum connection retries reached. Please check if the MQTT broker is running and accessible."
            print(error_msg)
            self.error_occurred.emit(error_msg)
            self.connection_status.emit(False)
            return

        try:
            print(f"Attempting to connect to MQTT broker at {self.config['broker']}:{self.config['port']} (Attempt {self.retry_count + 1}/{self.max_retries})")
            self.client.connect(self.config['broker'], self.config['port'])
            self.client.loop_start()
        except Exception as e:
            error_msg = f"Connection error: {e}. Please verify broker address and port."
            print(error_msg)
            self.error_occurred.emit(error_msg)
            self.retry_count += 1
            print(f"Retrying in {self.reconnect_delay} seconds (Attempt {self.retry_count + 1}/{self.max_retries})...")
            self._schedule_retry()

    def _schedule_retry(self):
        """Schedule a retry attempt"""
        from threading import Timer
        Timer(self.reconnect_delay, self._try_connect).start()
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.client.loop_stop()
        self.client.disconnect()
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to broker"""
        if rc == 0:
            print("Connected to MQTT broker")
            self.connected = True
            self.connection_status.emit(True)
            # Subscribe to the PLC's ENVIAR topic with QoS=1
            topic = self.config['topics']['receive']
            self.client.subscribe(topic, qos=1)
            self.pending_subscriptions.add(topic)
        else:
            error_msg = f"Connection failed with code {rc}"
            print(error_msg)
            self.error_occurred.emit(error_msg)
            self.connection_status.emit(False)
    
    def on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from broker"""
        self.connected = False
        self.subscriptions.clear()
        self.pending_subscriptions.clear()
        print("Disconnected from MQTT broker")
        self.connection_status.emit(False)
        if rc != 0:
            error_msg = "Unexpected disconnection. Attempting to reconnect..."
            print(error_msg)
            self.error_occurred.emit(error_msg)
            self._try_connect()
    
    def on_publish(self, client, userdata, mid):
        """Callback when a message is published"""
        print(f"Message {mid} has been published")
        # The actual delivery confirmation will be handled by the publish() result's wait_for_publish()
    
    def on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages
        
        Processes messages received from the A_ENVIAR topic.
        Expected message formats:
        
        1. Temperature update:
           {"tunnel_id": X, "temp_output": Y, "temp_external": Z, "temp_internal": W}
        
        2. Defrost status update:
           {"tunnel_id": X, "defrost_status": true/false}
        
        3. Running status update:
           {"tunnel_id": X, "running_status": true/false}
        
        Each message type triggers the corresponding signal to update the UI.
        """
        try:
            # Process messages from PLC's ENVIAR topic (A_ENVIAR)
            if msg.topic == self.config['topics']['receive']:
                try:
                    # Parse the JSON message
                    data = json.loads(msg.payload)
                    print(f"Received message on {msg.topic}: {data}")
                    
                    # Check if the message contains a tunnel ID
                    if 'tunnel_id' in data:
                        tunnel_id = int(data['tunnel_id'])
                        
                        # Process temperature update message
                        if all(key in data for key in ['temp_output', 'temp_external', 'temp_internal']):
                            print(f"Processing temperature update for tunnel {tunnel_id}")
                            self.temperature_updated.emit(
                                tunnel_id,
                                float(data['temp_output']),
                                float(data['temp_external']),
                                float(data['temp_internal'])
                            )
                        
                        # Process defrost status update message
                        if 'defrost_status' in data:
                            print(f"Processing defrost status update for tunnel {tunnel_id}: {data['defrost_status']}")
                            self.defrost_status_updated.emit(tunnel_id, bool(data['defrost_status']))
                        
                        # Process running status update message
                        if 'running_status' in data:
                            print(f"Processing running status update for tunnel {tunnel_id}: {data['running_status']}")
                            self.tunnel_status_updated.emit(tunnel_id, bool(data['running_status']))
                except json.JSONDecodeError:
                    print(f"Error decoding JSON message: {msg.payload}")
        except Exception as e:
            error_msg = f"Error processing message: {e}"
            print(error_msg)
            self.error_occurred.emit(error_msg)
    
    def set_temperature(self, tunnel_id, setpoint):
        """Set temperature setpoint for a tunnel
        
        Args:
            tunnel_id (int): The ID of the tunnel (1-12)
            setpoint (float): The temperature setpoint value
            
        Returns:
            bool: True if message was published successfully
            
        Message Format:
            SXX,YXXXX
            Where:
            - S is a constant
            - XX is the two-digit tunnel number
            - Y is the sign (+ or -)
            - XXXX is the four-character setpoint value including the decimal point
            Sent to topic: A_RECIBIR
        """
        if not self.client.is_connected():
            error_msg = "Cannot set temperature: Not connected to MQTT broker"
            print(error_msg)
            self.error_occurred.emit(error_msg)
            return False

        try:
            # Format tunnel number as two digits
            tunnel_str = f"{tunnel_id:02d}"
            
            # Format setpoint with sign and ensure it's exactly 4 characters including decimal point
            sign = '+' if setpoint >= 0 else '-'
            abs_value = abs(setpoint)
            
            # Format the value to ensure it's exactly 4 characters including decimal point
            # Examples: 12.3, 1.23, 0.12, etc.
            value_str = f"{abs_value}"
            
            # Ensure the value string is exactly 4 characters
            # If it's shorter than 4 characters, pad with zeros to the right
            # If it's longer than 4 characters, truncate it
            if len(value_str) < 4:
                value_str = value_str.ljust(4, '0')
            elif len(value_str) > 4:
                value_str = value_str[:4]
            
            # Construct the message in required format: SXX,YXXXX
            message = f"S{tunnel_str},{sign}{value_str}"
            
            # Get the topic from config (A_RECIBIR)
            topic = self.config['topics']['send']
            
            # Send the raw message directly without JSON wrapping
            # Publish the message with QoS=1 (at least once delivery) and retain flag set to true
            result = self.client.publish(topic, message, qos=1, retain=True)
            
            # Check if the message was queued for publishing (rc=0 means success)
            # is_published() can give false negatives as it only checks if published immediately
            # not if it was queued successfully
            if result.rc == 0:
                success = True
                print(f"Successfully queued setpoint {message} to {topic}")
            else:
                success = False
                error_msg = f"Failed to publish setpoint {message} to {topic}, error code: {result.rc}"
                print(error_msg)
                self.error_occurred.emit(error_msg)
                
            return success
        except Exception as e:
            error_msg = f"Error setting temperature: {e}"
            print(error_msg)
            self.error_occurred.emit(error_msg)
            return False
    
    def send_command(self, tunnel_id, command, message=None):
        """Send command for a tunnel with optional custom message
        
        Args:
            tunnel_id (int): The ID of the tunnel (1-12)
            command (str): Command type ('start', 'stop', 'defrost')
            message (str, optional): Custom message to send. If None, uses config default.
            
        Returns:
            bool: True if message was published successfully
            
        Message Format:
            {"type": "command", "tunnel_id": X, "value": "XX,X,X"}
            Where XX is the two-digit tunnel number, and X,X are the fan and PID values
            Sent to topic: A_RECIBIR
        """
        if not self.client.is_connected():
            print("Cannot send command: Not connected to MQTT broker")
            return False

        # Get the topic from config (A_RECIBIR)
        topic = self.config['topics']['send']
        
        # Format the tunnel number as two digits
        tunnel_str = f"{tunnel_id:02d}"
        
        # Determine the fan and PID values based on the command
        if command == 'start':
            # For start command: fan=1, PID=1
            value = f"{tunnel_str},1,1"
        elif command == 'stop':
            # For stop command: fan=0, PID=0
            value = f"{tunnel_str},0,0"
        elif command == 'defrost':
            # For defrost command, use the provided message format (XX,X,0)
            # This should be in the format: XX,1,0 for defrost ON or XX,0,0 for defrost OFF
            # Where XX is the two-digit tunnel number
            value = message if message else self.config['messages'].get(command, command)
        else:
            # For other commands, use the original message or config default
            value = message if message else self.config['messages'].get(command, command)
        
        # Send the raw message directly without JSON wrapping
        # Publish the message with QoS=1 (at least once delivery) and retain flag set to true
        result = self.client.publish(topic, value, qos=1, retain=True)
        success = result.is_published()
        
        print(f"Publishing command to {topic}. Message: {value}. Success: {success}")
        return success