robot_id = 'rob-003'
mqtt_options = {
    'clientId': 'client-robot-rob-003',  # Replace with your robot's client ID
    'username': 'robotclient',  # Replace with your HiveMQ Cloud username
    'password': 'Robothive@234',  # Replace with your HiveMQ Cloud password
    'broker': '65f02f33157749ed9e713a070f930f6e.s1.eu.hivemq.cloud',  # Replace with your HiveMQ Cloud cluster URL
    'port': 8883,  # HiveMQ Cloud port (usually 8883 for TLS)
    'keepalive': 60  # Keepalive interval in seconds
}