"""
This is the peer to peer file sharing client.
"""

import socket
import random
import time
import os
import sys
import threading
import hashlib

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
                print("request (Run file request)")
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
            case "request":
                peer_port = int(input("Enter peer port to request from: "))
                file_name = input("Enter file name to request: ")
                request(peer_port, file_name)
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
            elif data.decode().startswith("REQUEST"):
                print("Received Request")
                try:
                    _, receiver_port, file_name = data.decode().split("<SEPARATOR>")
                    file_path = os.path.join(sys.argv[1], file_name)
                    sender_thread = threading.Thread(target=sender, args=(file_path, LOCAL_HOST, int(receiver_port)+100))
                    sender_thread.start()
                except Exception as e:
                    print(f"Error handling file request {e}")
            conn.close()
        except:
            pass


def request(peer_port, file_name):
    recv_thread = threading.Thread(target=receiver, args=(LOCAL_HOST, running_port + 100, file_name))
    recv_thread.start()
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            print("sent request")
            s.connect((LOCAL_HOST, peer_port))
            request_message = f"REQUEST<SEPARATOR>{running_port}<SEPARATOR>{file_name}"
            s.sendall(request_message.encode())
    except Exception as e:
        print(f"Failed to request file {e}")

    recv_thread.join()


BUFFER_SIZE = 4096

def sender(file_path, receiver_ip, receiver_port):
    filesize = os.path.getsize(file_path)
    filename = os.path.basename(file_path)

    with open(file_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((receiver_ip, receiver_port))

        metadata = f"{filesize}<SEPARATOR>{file_hash}<SEPARATOR>"
        metadata = metadata.ljust(BUFFER_SIZE, '#')
        s.sendall(metadata.encode())

        with open(file_path, "rb") as f:
            chunk_count = 0
            while True:
                chunk = f.read(BUFFER_SIZE)
                if not chunk:
                    break
                s.sendall(chunk)
                chunk_count += 1

        print(f"{filename} sent in {chunk_count} chunks, hash: {file_hash}")


def receiver(bind_ip, bind_port, file_name):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((bind_ip, bind_port))
        s.listen(1)
        print(f"Listening on {bind_ip}:{bind_port}")


        conn, addr = s.accept()
        print(f"Connection from {addr}")

        metadata = conn.recv(BUFFER_SIZE).decode()
        filesize, expected_hash, _ = metadata.split("<SEPARATOR>")
        filesize = int(filesize)
        output_name = os.path.join("received", file_name)

        with open(output_name, "wb") as f:
            received = 0
            chunk_count = 0
            while received < filesize:
                chunk = conn.recv(min(BUFFER_SIZE, filesize - received))
                if not chunk:
                    break
                f.write(chunk)
                received += len(chunk)
                chunk_count += 1

        with open(output_name, "rb") as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest()

        if actual_hash == expected_hash:
            print(f"File received in {chunk_count} chunks, hash: {actual_hash}")
        else:
            print(f"File received but hash mismatch, expected {expected_hash} but got {actual_hash}")


if __name__ == "__main__":
    main()