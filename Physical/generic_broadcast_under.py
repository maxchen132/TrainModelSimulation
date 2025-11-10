import socket
import time

# --- Placeholder Network Configuration ---
# You MUST replace these values with the actual network configuration of your server.

# 1. IP address assigned to your 'UNDER' interface.
# The socket will be bound to this specific interface.
UNDER_IP = '192.168.1.100'

# 2. The standard port number for the application traffic.
PORT = 50000

# 3. The subnet's broadcast address (usually ends in .255).
# Received data will be resent to this address.
BROADCAST_IP = '192.168.1.255'

# 4. Max size of the data packet we can receive.
BUFFER_SIZE = 1024

def setup_socket():
    """Initializes and configures the UDP socket."""
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Enable address reuse (useful for testing/restarting quickly)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Enable broadcast mode on the socket
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    # Bind the socket to the specific IP address of the UNDER interface and the port
    # This makes the socket listen specifically on the UNDER interface.
    try:
        sock.bind((UNDER_IP, PORT))
        print(f"[*] Bound to interface {UNDER_IP} on port {PORT}. Ready to receive broadcasts.")
    except Exception as e:
        print(f"[!] Error binding socket: {e}")
        print(f"[!] Please ensure {UNDER_IP} is the correct IP for the 'UNDER' interface.")
        return None
        
    return sock

def broadcast_forwarder():
    """Listens for data and rebroadcasts it."""
    sock = setup_socket()
    if not sock:
        return

    while True:
        try:
            # 1. Receive data from the network
            data, addr = sock.recvfrom(BUFFER_SIZE)
            
            message = data.decode('utf-8', errors='ignore').strip()
            
            # Prevent echoing its own forwarded packet immediately (simple check)
            # This is a basic filter; more advanced logic might be needed for complex loops.
            if addr[0] == UNDER_IP:
                # This is likely a packet sent by this machine, or on the local interface.
                # We can choose to ignore it or process it. For a simple forwarder, we skip.
                continue

            current_time = time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{current_time}] Received {len(data)} bytes from {addr[0]}:{addr[1]}: '{message}'")
            
            # 2. Re-broadcast the received data
            # The data is sent to the network's broadcast address.
            # Since the socket is bound to UNDER_IP, the system usually routes it out the UNDER interface.
            sock.sendto(data, (BROADCAST_IP, PORT))
            print(f"    --> Re-broadcasted data to {BROADCAST_IP}:{PORT}")

        except KeyboardInterrupt:
            print("\n[!] Shutting down forwarder.")
            break
        except Exception as e:
            print(f"[!] An error occurred: {e}")
            time.sleep(1) # Wait briefly before retrying

    sock.close()

if __name__ == "__main__":
    broadcast_forwarder()