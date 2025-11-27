#!/usr/bin/env python3
import socket
import json

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Listen on all interfaces, port 5000
sock.bind(("0.0.0.0", 5000))

print("Listening for JSON broadcast...")

while True:
    msg, addr = sock.recvfrom(65535)
    try:
        data = json.loads(msg.decode())
        print(f"Received from {addr}: {data}")
    except:
        print(f"Non-JSON data received: {msg}")
