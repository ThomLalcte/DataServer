import socket

s = socket.socket()
s.connect(("192.168.0.139",10000))
s.send(b"stop")
response = s.recv(2)
s.close()
print(response)