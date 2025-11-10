import socket
import time

# --- Placeholder Network Configuration ---
# You MUST replace this value with the actual IP of your 'MAIN' interface.
MAIN_IP = '10.0.0.100'

# This port must match the port you expect data on.
PORT = 50000

# Buffer size
BUFFER_SIZE = 1024

def setup_main_socket():
    """Initializes and configures the UDP socket for the MAIN interface."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Enable address reuse
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # --- Critical Step for Interface-Specific Listening ---
    # Bind the socket *only* to the IP address of the MAIN interface.
    # It will ignore all traffic from the UNDER interface.
    try:
        sock.bind((MAIN_IP, PORT))
        print(f"[*] Bound to MAIN interface {MAIN_IP} on port {PORT}.")
        print("[*] Waiting for data on the MAIN network...")
    except Exception as e:
        print(f"[!] Error binding socket: {e}")
        print(f"[!] Please ensure {MAIN_IP} is the correct IP for the 'MAIN' interface.")
        return None
        
    return sock

def start_listening():
    """Listens for data on the MAIN interface and prints it."""
    sock = setup_main_socket()
    if not sock:
        return

    while True:
        try:
            # Wait and receive data
            data, addr = sock.recvfrom(BUFFER_SIZE)
            
            message = data.decode('utf-8', errors='ignore').strip()
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"[{current_time}] Received MAIN data from {addr[0]}:{addr[1]} -> '{message}'")

        except KeyboardInterrupt:
            print("\n[!] Shutting down listener.")
            break
        except Exception as e:
            print(f"[!] An error occurred: {e}")

    sock.close()

if __name__ == "__main__":
    start_listening()