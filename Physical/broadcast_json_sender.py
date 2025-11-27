#!/usr/bin/env python3
import socket
import json

data = {
    "type": "status",
    "message": "Hello from server A",
    "value": 42
}

# Convert Python dict to JSON string
json_data = json.dumps(data)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Enable broadcast option
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# Broadcast address for subnet 192.168.0.0/24
broadcast_addr = ("192.168.0.255", 5000)

sock.sendto(json_data.encode(), broadcast_addr)

print("JSON broadcast sent!")
