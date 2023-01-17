import socket
import sys
import time
# Create a TCP/IP socket


def initServer():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind the socket to the port
    server_address = ('192.168.1.35', 8002)
    print('starting up on {} port {}'.format(*server_address))
    sock.bind(server_address)
    sock.listen(1)
    return sock


# Listen for incoming connections
i = 0
print('waiting for a connection')
connection, client_address = sock.accept()
while True:
    # Wait for a connection
    a = connection.recv(16)
    if len(a) == 0:
        continue
    print("took %.02f ms" % ((int(time.time()*1000)-int(a))))
