import socket
import time

# --- Configuration ---
# This port must match the port used by the forwarder.
PORT = 50000

# Buffer size
BUFFER_SIZE = 1024

def setup_listener_socket():
    """Initializes and configures the UDP socket to receive broadcasts."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Enable address reuse
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # --- Critical Step for Receiving Broadcasts ---
    # Bind to '' (INADDR_ANY or 0.0.0.0), which means "listen on all interfaces".
    # This is the standard way to receive broadcast packets, as they are
    # not sent to a specific IP address but to the whole network.
    try:
        sock.bind(('', PORT))
        print(f"[*] Broadcast listener bound to all interfaces on port {PORT}.")
        print("[*] Waiting for broadcast data...")
    except Exception as e:
        print(f"[!] Error binding socket: {e}")
        return None
        
    return sock

def start_listening():
    """Listens for data and prints it."""
    sock = setup_listener_socket()
    if not sock:
        return

    while True:
        try:
            # Wait and receive data
            data, addr = sock.recvfrom(BUFFER_SIZE)
            
            message = data.decode('utf-8', errors='ignore').strip()
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"[{current_time}] Received broadcast from {addr[0]}:{addr[1]} -> '{message}'")

        except KeyboardInterrupt:
            print("\n[!] Shutting down listener.")
            break
        except Exception as e:
            print(f"[!] An error occurred: {e}")

    sock.close()

if __name__ == "__main__":
    start_listening()