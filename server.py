import socket
import sys

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# Bind the socket to the port
server_address = ('192.168.1.35', 8001)
print('starting up on {} port {}'.format(*server_address))
sock.bind(server_address)

# Listen for incoming connections
sock.listen(1)
i = 0
print('waiting for a connection')
connection, client_address = sock.accept()
while True:
    # Wait for a connection

    connection.recv(16)
    print('connection from', client_address)
    # Receive the data in small chunks and retransmit it
    connection.sendall(str(i).encode())

    i += 1
