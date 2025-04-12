"""
This is the peer to peer file sharing client.
"""

import socket
import random
import time
import signal

sock = None
PORT_RANGE = (50000,59999)

def main():
    """
    The main program for this module
    """
    global sock
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True: ## loop until socket binds to some port
        try:
            random_port = random.randint(PORT_RANGE[0], PORT_RANGE[1])
            sock.bind(('127.0.0.1', random_port))
            print(f"Socket running on port {random_port}")
            break
        except:
            print(f"Port {random_port} is busy, trying another")

    while True:
        time.sleep(1)

def handle_sigint(signum, frame):
    """
    Handles a keyboard interrupt, closes the socket
    """
    global sock

    if sock is not None:
        sock.close()
    print("Closing socket and exiting...")
    exit(0)

signal.signal(signal.SIGINT, handle_sigint)

if __name__ == "__main__":
    main()