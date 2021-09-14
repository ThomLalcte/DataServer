from os import name
import threading
import socket

import json as js
from datetime import datetime as dt
from datetime import timedelta as dtd

import matplotlib.pyplot as plt
import calendar as cal

#slep handler
class slepHandler (threading.Thread):
    def __init__(self,state):
        threading.Thread.__init__(self)
        self.state = state

    def run(self):
        today = str(dt.now().year) + "-" + str(dt.now().month) + "-" + str(dt.now().day)
        r = self.state #int.from_bytes(self.state, "big") 
        with open("slep_data.json", "r+") as file:

            data = js.load(file)

            if today in data:   #aquisition de données
                if len(data[today]) > dt.now().hour:
                    data[today][dt.now().hour].append(int(r))
                else:
                    while dt.now().hour-1 > len(data[str(dt.now().year) + "-" + str(dt.now().month) + "-" + str(dt.now().day)]):
                        data[today].append([-1])
                    data[today].append([int(r)])
            else:
                data.update({today:[[int(r)]]})

            file.seek(0)
            js.dump(data, file)
            file.close()
            # if dt.now().minute < 3:
            #     self.processData()

        return

    def processData(self):
        span = 12        #étendue du graphique
        x = []
        y = []
        today = str(dt.now().year) + "-" + str(dt.now().month) + "-" + str(dt.now().day)
        now = dt.now().hour

        with open("slep_data.json", "r+") as file:
            data = js.load(file)
            file.close()

        if now-span >= 0: #cas où l'interval est compris dans la journée actuelle
            if now > len(data[today]):
                print("Error: insuffiscient hour data to process")

            else:
                for i in range(now-span,now):
                    g = 0.0
                    gg = 1/len(data[today][i])
                    for key in data[today][i]: 
                        x.append(key)
                        y.append(i+g)
                        g += gg

        if now-span < 0:#cas où l'interval est compris entre aujourd'hui et hier

            jouraregarder = str(dt.now().year) + "-" + str(dt.now().month) + "-" + str(dt.now().day-1)
            if dt.now().day-1 == 0: #cas où le jour précédent est dans un autre mois
                wkd, nday = cal.monthrange(dt.now().year,dt.now().month-1)
                jouraregarder = str(dt.now().year) + "-" + str(dt.now().month-1) + "-" + str(nday)

            if now > len(data[today]):
                print("Error: insuffiscient hour data to process")

            elif not jouraregarder in data:
                print("Error: no previous day data to process")
                
            elif 23 > len(data[jouraregarder]):
                print("Error: insuffiscient previous day's hour data to process")

            else: 
                for i in range(23+now-span,23):
                    g = 0.0 #pour la graduation
                    gg = 1/len(data[jouraregarder][i])

                    for key in data[jouraregarder][i]: 
                        x.append(key)
                        y.append(i-23+g)
                        g+=gg

                for i in range(0,now):
                    g = 0.0 #pour la graduation
                    gg = 1/len(data[today][i])

                    if i >= len(data[today]):
                        print("Error: insuffiscient hour data to process")
                        break

                    for key in data[today][i]: #iteration des tranches de 5 min de l'heure i
                        x.append(key)
                        y.append(i+g)
                        g+=gg

        plt.plot(y,x)
        #plt.show()
        #plt.savefig("yabro.png",dpi=250)
        plt.savefig("C:\inetpub\wwwroot\yabro.png",dpi=250)
        plt.clf()

#mood handler
class moodHandler (threading.Thread):
    def __init__(self,mood):
        threading.Thread.__init__(self)
        self.mood = mood

    def run(self):
        liveup = str(dt.now().hour) + ":" + str(dt.now().minute)
        stuff = int.from_bytes(self.mood, "big")
        print(stuff)
        with open("mood_data.json", "r+") as file:
            today = str(dt.now().year) + "-" + str(dt.now().month) + "-" + str(dt.now().day)
            
            data = js.load(file)

            if today in data:   #aquisition de données
                    data[today].append([liveup,stuff])
                    
            else:
                data.update({today:[[liveup,stuff]]})

            print(data[today][-2:])
            file.seek(0)
            js.dump(data, file)
            file.close()
        return

#log handler
class logHandler (threading.Thread):
    def __init__(self,state):
        threading.Thread.__init__(self)
        self.state = state

    def run(self):
        liveup = str(dt.now().hour) + ":" + str(dt.now().minute)
        stuff = self.state.decode("utf-8") 
        with open("log_data.json", "r+") as file:
            today = str(dt.now().year) + "-" + str(dt.now().month) + "-" + str(dt.now().day)
            
            data = js.load(file)

            if today in data:   #aquisition de données
                    data[today].append([liveup,stuff])
                    
            else:
                data.update({today:[[liveup,stuff]]})

            print(data[today][-2:])
            file.seek(0)
            js.dump(data, file)
            file.close()
        return


s = socket.socket()         

s.bind(('0.0.0.0', 10000 ))
s.listen(0)
errors = 0
errors_names = [] 

def lookForErrors(name):
    present = False
    for error_name in errors_names:
        if error_name == name:
            present = True
    if not present:
        errors_names.append(name)

"""
sleph = slepHandler(5)
sleph.processData()

"""
while True:
    try:
        client, addr = s.accept()
        content = client.recv(32)
        client_name = client.getpeername()        
        print("Closing connection")

        #slep handler
        if content == b"slep":
            interval = 3
            if dt.now()<(dt.now()).replace(hour=9,minute=2) and dt.now() >= (dt.now()).replace(hour=8,minute=56):
                client.send(int.to_bytes(((dt.now()).replace(hour=9,minute=4)-dt.now()).total_seconds(),2,"big",signed=False))
                print(((dt.now()).replace(hour=9,minute=4)-dt.now()).total_seconds())
            else:
                client.send(int.to_bytes((interval-dt.now().minute%interval)*60-dt.now().second,2,"big",signed=False))
            # client.send(int.to_bytes(1234,2,"big",signed=False))
            # print(int.to_bytes(1234,2,"big",signed=False))
            slepQte = client.recv(4)
            client.shutdown(socket.SHUT_RDWR)
            client.close()
            print("slep repport: ",slepQte)#int.from_bytes(content, "big"))
            sleph = slepHandler(int.from_bytes(slepQte, "big"))
            sleph.start()

        #log handler
        elif content == b"unlk_lptp":
            client.send(b"online")
            client.shutdown(socket.SHUT_RDWR)
            client.close()
            #print("logged on toaster à fromage")
            logh = logHandler(content)
            logh.start()
        elif content == b"lk_lptp":
            client.shutdown(socket.SHUT_RDWR)
            client.close()
            #print("logged off toaster à fromage")
            logh = logHandler(content)
            logh.start()

        #mood handler
        elif content == b"mood":
            client.send(b"ok")
            curent_mood = client.recv(32)
            client.shutdown(socket.SHUT_RDWR)
            client.close()
            moodh = moodHandler(curent_mood)
            moodh.start()
        
        #stop handler
        elif content == b"stop":
            client.send(b"ok")
            client.shutdown(socket.SHUT_RDWR)
            print("stop command recived from: ",client.getpeername())
            client.close()
            print("Stopping server")
            break

        #ping handler
        elif content == b"ping":
            client.send(b"toe ta dlair dun ping")
            client.shutdown(socket.SHUT_RDWR)
            print("Ping command recived from: ",client.getpeername())
            client.close()

        else:
            errors+=1
            command = content.decode("utf-8")
            print("unknown command (" + command + ") from: ")
            print(client_name)
            lookForErrors(command)
                    
    except TimeoutError:
        print("Client timed-out")
        errors+=1
        lookForErrors("TimeoutError")
    except ConnectionResetError:
        print("Client badly closed socket")
        errors+=1
        lookForErrors("ConnectionResetError")

#server logs
with open("server_log_data.json", "r+") as file:
        today = str(dt.now().year) + "-" + str(dt.now().month) + "-" + str(dt.now().day)
        
        data = js.load(file)

        data.update({today:[errors,errors_names]})

        #print(data[today][-2:])
        file.seek(0)
        js.dump(data, file)
        file.close()