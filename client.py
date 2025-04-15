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

    if not os.path.isfile(file_dir + "\\index.txt"):
        print("Index file does not exist in provided directory!!")
        sys.exit(1)

    global sock
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True: ## loop until socket binds to some port
        try:
            random_port = random.randint(PORT_RANGE[0], PORT_RANGE[1])
            sock.bind(('127.0.0.1', random_port))
            sock.listen()
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