"""
This is the peer to peer file sharing client.
"""

import socket
import random
import time
import signal
import os
import sys

sock = None
LOCAL_HOST = '127.0.0.1'
PORT_RANGE = (50000,59999)

def main():
    """
    The main program for this module
    """
    if len(sys.argv) < 2:
        print("Provide a file directory to read from")
        sys.exit(1)

    file_dir = sys.argv[1]
    if not os.path.isdir(file_dir):
        print(f"\'{file_dir}\' is NOT a valid directory")
        sys.exit(1)

    global sock
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True: ## loop until socket binds to some port
        try:
            random_port = random.randint(PORT_RANGE[0], PORT_RANGE[1])
            sock.bind((LOCAL_HOST, random_port))
            sock.listen()
            print(f"Socket running on port {random_port}")
            break
        except:
            print(f"Port {random_port} is busy, trying another")

    while True:
        conn, addr = sock.accept()

        with conn:
            print(f"Connected by {addr}")

            while True:
                data = conn.recv(1024)
                if not data:
                    print("Connection was closed")
                    conn.close()
                    break
                print(f"Received: {data.decode()}")

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