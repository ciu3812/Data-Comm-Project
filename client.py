"""
This is the peer to peer file sharing client.
"""

import socket
import random
import time
import os
import sys
import threading

## Constants
LOCAL_HOST = '127.0.0.1'
PORT_RANGE = (50000,50040) ## Inclusive range
PEER_DISCOVERY_TIMEOUT = 10
PEER_DISCOVERY_MAX = 5

sock = None
running_port = 0 ## The port this client is running on
print_lock = threading.Lock()
broadcast_end_event = threading.Event()

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

    global sock, running_port
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True: ## loop until socket binds to some port
        try:
            random_port = random.randint(PORT_RANGE[0], PORT_RANGE[1])
            sock.bind((LOCAL_HOST, random_port))
            sock.listen()
            print(f"Socket running on port {random_port}")
            running_port = random_port
            break
        except:
            pass # do nothing, try another port

    broadcast_t = threading.Thread(target=broadcast)
    broadcast_t.start()

    print("This is peer to peer file sharing system!!")
    print("Enter \'help\' for a list of helpful commands")
    while True:
        msg = input(" -> ")
        match msg:
            case "help":
                print("help (Print this help message)")
                print("exit (Close this client)")
                print("d (Run peer discovery)")
            case "exit":
                broadcast_end_event.set()
                broadcast_t.join()
                sock.close()
                print("Exiting...")
                break
            case "d":
                peers = peer_discovery()
                if len(peers) > 0:
                    for i in range(len(peers)):
                        print(f"{i + 1}: {peers[i]}")
                else:
                    print("No peers were discovered")
            case _:
                print("Not a recognized command")

def peer_discovery():
    """
    Discovers valid peers in the network, up to a limit
    """
    peers = [] ## A list of ports that contain valid peers
    curr_port = PORT_RANGE[0]
    while curr_port < PORT_RANGE[1] + 1 and len(peers) < PEER_DISCOVERY_MAX:
        if curr_port != running_port: # Don't try to connect to yourself
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.05) ## low timeout because on localhost
                s.connect((LOCAL_HOST, curr_port))
                s.sendall(b'PEER')
                s.settimeout(1) # to a whole second to wait for the handshake
                data = s.recv(64)
                if data.decode() == "PEER":
                    peers.append(curr_port)
                    s.close()
            except:
                pass
        curr_port += 1
    return peers

def broadcast():
    """
    Broadcasts to incoming connections that this is a valid peer
    """
    sock.setblocking(False)
    sock.settimeout(2)
    while not broadcast_end_event.is_set():
        try:
            conn, addr = sock.accept()
            data = conn.recv(64)
            if data.decode() == "PEER":
                conn.sendall(b'PEER')
            conn.close()
        except:
            pass

if __name__ == "__main__":
    main()