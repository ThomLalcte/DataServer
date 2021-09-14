import socket

s = socket.socket()
s.connect(("localhost",10000))
s.send(b"stop")
response = s.recv(2)
s.close()
print(response)