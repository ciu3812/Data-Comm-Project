import socket
import threading
import hashlib
import os
import sys
import time

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

def main():
    file_name = "coconut.jpg"
    file_name = "test.txt"
    ip = "127.0.0.1"
    port = 5001

    recv_thread = threading.Thread(target=receiver, args=(ip, port, file_name))
    recv_thread.start()

    time.sleep(1)

    send_thread = threading.Thread(target=sender, args=(file_name, ip, port))
    send_thread.start()

    recv_thread.join()
    send_thread.join()

if __name__ == "__main__":
    main()