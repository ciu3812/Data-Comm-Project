"""
Peer to Peer File Sharing client

This is the peer to peer file sharing client.

Caleb Underkoffler
Damon Gonzalez
Data Comm & Network
Project
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
BUFFER_SIZE = 4096

sock = None
running_port = 0 ## The port this client is running on
print_lock = threading.Lock()
listener_end_event = threading.Event()


def main():
    """
    The main program and entry point for this module
    Handles user interaction and commands
    """

    #error catching
    if len(sys.argv) < 2:
        print("Provide a file directory to read from")
        sys.exit(1)

    file_dir = sys.argv[1]
    if not os.path.isdir(file_dir):
        print(f"\'{file_dir}\' is NOT a valid directory")
        sys.exit(1)

    global sock, running_port
    
    #bind user to a port
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

    #start listener
    listener_t = threading.Thread(target=listener)
    listener_t.start()

    peers = []

    #run command line interface
    print("This is peer to peer file sharing system!!")
    print("Enter \'help\' for a list of helpful commands")
    while True:
        msg = input(" -> ")
        match msg:
            case "help":
                print("help (Print this help message)")
                print("exit (Close this client)")
                print("discover (Run peer discovery)")
                print("peers (Show peers currently stored)")
                print("index (Show files from specific peer)")
                print("request (Request specific file from specific peer)")
                
            case "exit":
                listener_end_event.set()
                listener_t.join()
                sock.close()
                print("Exiting...")
                break
            case "discover":
                peers = peer_discovery()
                if len(peers) > 0:
                    for i in range(len(peers)):
                        print(f"{i + 1}: {peers[i]}")
                else:
                    print("No peers were discovered")
            case "peers":
                if len(peers) > 0:
                    for i in range(len(peers)):
                        print(f"{i + 1}: {peers[i]}")
                else:
                    print("No peers are stored")
            case "request":
                peer_port = int(input("Enter peer port to request from: "))
                file_name = input("Enter file name to request: ")
                destination = input("Enter destination to save file to: ")
                request(peer_port, file_name, destination)
            case "index":
                peer_port = int(input("Enter peer port to see files from: "))
                index(peer_port)
            case _:
                print("Not a recognized command")


def peer_discovery():
    """
    Discovers valid peers in the network, up to a limit

    Returns:
        list[int]: a list of active peer ports
    """
    peers = [] ## A list of ports that contain valid peers

    #start timer for timeout
    start = int(time.time())

    #loop through random ports until we find all peers, reach limit of peers, or timeout
    while int(time.time()) - start < PEER_DISCOVERY_TIMEOUT and len(peers) < PEER_DISCOVERY_MAX:
        curr_port = random.randint(PORT_RANGE[0], PORT_RANGE[1])
        if curr_port not in peers and curr_port != running_port: # Don't try to connect to yourself
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
    return peers


def listener():
    """
    Listens for incoming messages from peers and handles them:
    - Responds to "PEER" handshake for discovery.
    - Handles file transfer "REQUEST" and starts a sender thread.
    - Responds to "INDEX" requests with the list of available files.
    """
    sock.setblocking(False)
    sock.settimeout(2)
    while not listener_end_event.is_set():
        try:
            conn, addr = sock.accept()
            data = conn.recv(64)

            #handle discovery
            if data.decode() == "PEER":
                print("Received Discover Request")
                conn.sendall(b'PEER')
            #handle request
            elif data.decode().startswith("REQUEST"):
                print("Received Request To Download File")
                try:
                    _, receiver_port, file_name = data.decode().split("<SEPARATOR>")
                    file_path = os.path.join(sys.argv[1], file_name)
                    sender_thread = threading.Thread(target=sender, args=(file_path, LOCAL_HOST, int(receiver_port)+100))
                    sender_thread.start()
                except Exception as e:
                    print(f"Error handling file request {e}")
            #handle index
            elif data.decode() == "INDEX":
                print("Receive Index Request")
                files = os.listdir(sys.argv[1])
                response = "<SEPARATOR>".join(files)
                conn.sendall(response.encode())
            conn.close()
        except:
            pass


def request(peer_port, file_name, destination):
    """
    Requests a file from a peer and starts a receiver to download the file to specified location.

    Args:
        peer_port (int): Peer's port to request the file from.
        file_name (str): Name of the file to request.
        destination (str): Local path to save the file once downloaded.
    """
    #start receiver thread
    recv_thread = threading.Thread(target=receiver, args=(LOCAL_HOST, running_port + 100, file_name, destination))
    recv_thread.start()
    
    #send a request message to peer
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            print("sent request")
            s.connect((LOCAL_HOST, peer_port))
            request_message = f"REQUEST<SEPARATOR>{running_port}<SEPARATOR>{file_name}"
            s.sendall(request_message.encode())
    except Exception as e:
        print(f"Failed to request file {e}")

    recv_thread.join()


def sender(file_path, receiver_ip, receiver_port):
    """
    Sends a file to a peer with metadata and hash verification.

    Args:
        file_path (str): Local path of the file to send.
        receiver_ip (str): The IP of the receiver.
        receiver_port (int): The port of the receiver.
    """
    filesize = os.path.getsize(file_path)
    filename = os.path.basename(file_path)

    #open file and proccess hash
    with open(file_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    #connect to receiver
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((receiver_ip, receiver_port))

        #put metadata together of size BUFFERSIZE
        metadata = f"{filesize}<SEPARATOR>{file_hash}<SEPARATOR>"
        metadata = metadata.ljust(BUFFER_SIZE, '#')
        s.sendall(metadata.encode())

        #send file in chunks
        with open(file_path, "rb") as f:
            chunk_count = 0
            while True:
                chunk = f.read(BUFFER_SIZE)
                if not chunk:
                    break
                s.sendall(chunk)
                chunk_count += 1

        print(f"{filename} sent in {chunk_count} chunks, hash: {file_hash}")


def receiver(bind_ip, bind_port, file_name, destination):
    """
    Receives a file from a peer, verifies its integrity, then saves it to specified location.

    Args:
        bind_ip (str): IP to bind the receiving socket.
        bind_port (int): Port to bind the receiving socket.
        file_name (str): Name of file to receive.
        destination (str): location to save the file.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((bind_ip, bind_port))
        s.listen(1)

        conn, addr = s.accept()

        #process metadata
        metadata = conn.recv(BUFFER_SIZE).decode()
        filesize, expected_hash, _ = metadata.split("<SEPARATOR>")
        filesize = int(filesize)
        output_name = os.path.join(destination, file_name)

        #recieve the file in chunks and save to destination
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

        #check file integrity
        with open(output_name, "rb") as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest()

        if actual_hash == expected_hash:
            print(f"File received in {chunk_count} chunks, hash: {actual_hash}")
        else:
            print(f"File received but hash mismatch, expected {expected_hash} but got {actual_hash}")


def index(peer_port):
    """
    Requests the list of available files from a given peer and prints them.

    Args:
        peer_port (int): The port of the peer to see files of.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            #request the list of files from peer
            s.connect((LOCAL_HOST, peer_port))
            s.sendall(b"INDEX")
            data = s.recv(64).decode()
            files = data.split("<SEPARATOR>")
            #print files
            print(f"Files on peer {peer_port}:")
            for file in files:
                print(f" - {file}")
    except Exception as e:
        print(f"Could not retrieve index from {peer_port} {e}")


if __name__ == "__main__":
    main()