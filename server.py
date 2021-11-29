import threading
import socket

import json as js
from datetime import datetime as dt
from datetime import timedelta as dtd
from matplotlib import pyplot as plt
from matplotlib import dates as pltd

#slep handler
class slepHandler (threading.Thread):
    def __init__(self,state):
        threading.Thread.__init__(self)
        self.state = state

    def run(self):
        today = dt.now().strftime("%Y-%m-%d")
        r = self.state
        with open("slep_data.json", "r+") as file:

            data = js.load(file)

            if today in data:   #aquisition de données
                if len(data[today]) > dt.now().hour:
                    data[today][dt.now().hour].append(int(r))
                else:
                    while dt.now().hour-1 > len(data[today]):
                        data[today].append([-1])
                    data[today].append([int(r)])
            else:
                data.update({today:[[int(r)]]})

            file.seek(0)
            js.dump(data, file)
            file.close()
        if dt.now().minute%30<2:
            self.processData()
        return
    
    def processData(self):

        with open("slep_data.json", "r+") as file:
            filedata = js.load(file)
            mean = round((filedata[dt.now().strftime("%Y-%m-%d")][9][1]+filedata[dt.now().strftime("%Y-%m-%d")][9][2])/2)
            filedata[dt.now().strftime("%Y-%m-%d")][9][1]=mean
            filedata[dt.now().strftime("%Y-%m-%d")][9][2]=mean  #45-47: pour dealler avec le bug de l'ordi qui prend plus de 3 min à reboot et crée donc des données avec un glitch
            for i in range(len(filedata[dt.now().strftime("%Y-%m-%d")])-1): #48-50: pour compenser pour les fois où on manque 1 donné
                while len(filedata[dt.now().strftime("%Y-%m-%d")][i])<20:
                    filedata[dt.now().strftime("%Y-%m-%d")][i].append(filedata[dt.now().strftime("%Y-%m-%d")][i][-1])
            file.seek(0)
            js.dump(filedata, file)
            file.close()
        
        data=[]
        time=[]
        for i in range(20,24):
            for ii in range(0,20):
                data.append(filedata[(dt.now()-dtd(1)).strftime("%Y-%m-%d")][i][ii])
                time.append((dt.now()-dtd(1)).replace(hour=i,minute=ii*3))
        for i in range(0,dt.now().hour):
            for ii in range(0,20):
                data.append(filedata[dt.now().strftime("%Y-%m-%d")][i][ii])
                time.append((dt.now()).replace(hour=i,minute=ii*3))
        del filedata; del i; del ii


        gaus=[]
        var=2
        width=10
        for i in range(-width,width+1):
            gaus.append(2.71828**(-(i**2/(2*var**2)))/(var*(2*3.1415)**0.5))
        filteredData = []
        for i in range(width):
            data.insert(0,data[0])
            data.append(data[-1])
        for i in range(width,len(data)-width):
            ng=len(gaus)
            tot=0
            for ii in range(ng):
                tot+=gaus[ii]*data[i+ii-round((ng-1)/2)]
            filteredData.append(tot)
        for i in range(width):
            data.pop(0)
            data.pop(-1)


        deriv=[]
        filteredData.append(filteredData[-1])
        for i in range(len(filteredData)-1):
            deriv.append(filteredData[i+1]-filteredData[i]+1272600)
        filteredData.pop(-1)

        # plt.plot(time,data)
        # plt.plot(time,filteredData)
        # plt.plot(time,deriv)
        # plt.gca().xaxis.set_major_formatter(pltd.DateFormatter('%H:%M'))
        # plt.show()

        del data; del filteredData

        toa = time[deriv.index(min(deriv))].strftime("%H:%M")   #time of arrival
        tod = time[deriv.index(max(deriv))].strftime("%H:%M")   #time of departure
        #tts = (time[deriv.index(max(deriv))]-time[deriv.index(min(deriv))])    #total time slept
        with open("slep_timestamps_data.json", "r+") as file:
            slepdata=js.load(file)
            today = dt.now().strftime("%Y-%m-%d")
            if today in slepdata:
                slepdata[today]=[toa,tod]
            else:
                slepdata.update({today:[toa,tod]})
            file.seek(0)
            js.dump(slepdata, file)
            file.close()
        return

        
#slepdata handler
class slepDataHandler (threading.Thread):
    def __init__(self, date, hour, client):
        threading.Thread.__init__(self)
        self.date = date
        self.hour = hour
        self.client = client

    def run(self):
        with open("slep_data.json", "r+") as file:
            data = js.load(file)
            file.close()
        try:
            date = self.date.decode("utf-8")
            hour = int.from_bytes(self.hour, "big")
            for i in data[date][hour]:
                client.send(int.to_bytes(i,4,"big",signed=False))
                
        except KeyError:
            client.send(b"keyerror")
        except IndexError:
            client.send(b"indexerror")
        client.shutdown(socket.SHUT_RDWR)
        client.close()

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


sleph = slepHandler(5)
sleph.processData()
del sleph

while True:
    try:
        client, addr = s.accept()
        content = client.recv(32)
        client_name = client.getpeername()

        #slep handler
        if content == b"slep":
            interval = 3
            client.send(int.to_bytes((interval-dt.now().minute%interval)*60-dt.now().second,2,"big",signed=False))
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

        #slep data request handler
        elif content == b"slepdata":
            client.send(b"ok")
            #format: (string jour, int heure)
            jour = client.recv(10)
            heure = client.recv(2)
            print("{}, {}h".format(jour.decode("utf-8"), int.from_bytes(heure, "big")))
            slepdh = slepDataHandler(jour,heure,client)
            slepdh.start()

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
if errors>0:
    with open("server_log_data.json", "r+") as file:
            today = str(dt.now().year) + "-" + str(dt.now().month) + "-" + str(dt.now().day)
            
            data = js.load(file)

            data.update({today:[errors,errors_names]})

            #print(data[today][-2:])
            file.seek(0)
            js.dump(data, file)
            file.close()