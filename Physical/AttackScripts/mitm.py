from scapy.all import IP, TCP, send

target_ip = "128.10.250.50"
target_port = 4000

payload = b"<T 100 1><H 100 1>"

ip = IP(dst=target_ip)
tcp = TCP(dport=target_port, flags="PA")  # PSH + ACK flags to push data

packet = ip / tcp / payload
send(packet)

