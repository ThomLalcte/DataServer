import contextlib
import datetime
import threading
import socket
import sys

import json as js
from datetime import datetime as dt
from datetime import timedelta as dtd
# from matplotlib import pyplot as plt
# from matplotlib import dates as pltd

meanHighValue = 1276000
meanLowValue = 1160574
threshold =meanLowValue+(meanHighValue-meanLowValue)/2
slepLastSample=0

def saveData(client: socket.socket):
    interval = 3
    client.send(int.to_bytes((interval-dt.now().minute%interval)*60-dt.now().second,2,"big",signed=False))
    slepQte = client.recv(4)
    client.close()
    r = int.from_bytes(slepQte, "big")
    print("slep repport: ",r)
    global slepLastSample
    slepLastSample = r
    today = dt.now().strftime("%Y-%m-%d")
    with open("slep_data.json", "r+") as file:

        data = js.load(file)

        if today in data:   #aquisition de données
            if len(data[today]) > dt.now().hour:
                data[today][dt.now().hour].append(int(r))
            else:
                while dt.now().hour-1 > len(data[today]):
                    data[today].append([-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1])
                data[today].append([int(r)])
        else:
            data.update({today:[[int(r)]]})

        file.seek(0)
        js.dump(data, file)
        file.close()
    if dt.now().minute%30<2:
        processData()
    return

def saveData2(client: socket.socket):
    interval = 3
    client.send(int.to_bytes((interval-dt.now().minute%interval)*60-dt.now().second,2,"big",signed=False))
    slepQte = client.recv(4)
    wiggleQte = client.recv(4)
    client.close()
    r = int.from_bytes(slepQte, "big")
    w = int.from_bytes(wiggleQte, "big")
    print("slep repport: ",r)
    global slepLastSample
    slepLastSample = r
    today = dt.now().strftime("%Y-%m-%d")
    with open("slep_data.json", "r+") as file:
        data = js.load(file)
        if today in data:   #aquisition de données
            if len(data[today]) > dt.now().hour:
                data[today][dt.now().hour].append(int(r))
            else:
                while dt.now().hour-1 > len(data[today]):
                    data[today].append([-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1])
                data[today].append([int(r)])
        else:
            data.update({today:[[int(r)]]})

        file.seek(0)
        js.dump(data, file)
        file.close()

    with open("wiggle_data.json", "r+") as file:
        data = js.load(file)
        if today in data:   #aquisition de données
            if len(data[today]) > dt.now().hour:
                data[today][dt.now().hour].append(int(w))
            else:
                while dt.now().hour-1 > len(data[today]):
                    data[today].append([-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1])
                data[today].append([int(w)])
        else:
            data.update({today:[[int(w)]]})

        file.seek(0)
        js.dump(data, file)
        file.close()

    if dt.now().minute%30<2:
        processData()

def filterData(unfiltered):
    gaus=[]
    var=5
    width=20
    for i in range(-width,width+1):
        gaus.append(2.71828**(-(i**2/(2*var**2)))/(var*(2*3.1415)**0.5))
    filtered = []
    for i in range(width):
        unfiltered.insert(0,unfiltered[0])
        unfiltered.append(unfiltered[-1])
    for i in range(width,len(unfiltered)-width):
        ng=len(gaus)
        tot=0
        for ii in range(ng):
            tot+=gaus[ii]*unfiltered[i+ii-round((ng-1)/2)]
        filtered.append(tot)
    return filtered

def derivData(underived):
    derived=[]
    underived.append(underived[-1])
    for i in range(len(underived)-1):
        derived.append(underived[i+1]-underived[i])
    del underived[-1]
    return derived

def meanData(data):
    return sum(data)/len(data)

def isThomInBed(client: socket.socket):
    client.send(b"ok")
    client.send(int.to_bytes(slepLastSample<threshold,1,"big"))
    print("itib call from {}".format(client.getpeername()))
    client.close()

def processData():
    today = dt.now().strftime("%Y-%m-%d")
    hier = (dt.now()-dtd(1)).strftime("%Y-%m-%d")
    with open("slep_data.json", "r+") as file:
        filedata:dict = js.load(file)
        # tapon de code qui sert à réparer les données. Jespère que t content que je l'ai fait pour toi
        if (dt.now().hour==10):
            mean=filedata[today][9][1]+filedata[today][9][2]
            filedata[today][9][1:3]=[int(mean/2), int(mean/2)]
        if not hier in filedata:
            fill = []
            for i in range(dt.now().hour):
                fill+=[[-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]]
            filedata.update({hier:fill})
        if not today in filedata:
            fill = []
            for i in range(dt.now().hour):
                fill+=[[-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]]
            filedata.update({today:fill})
        if len(filedata[hier])<24:
            for i in len(filedata[hier]):
                while len(i)<20:
                    i.append(-1)
            while len(filedata[hier])<24:
                filedata[hier].append([-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1])
        for i in filedata[hier]:
            if len(i)<20:
                for ii in range(20-len(i)):
                    i.append(-1)
        if len(filedata[today])<dt.now().hour+1:
            for i in filedata[today]:
                while len(i)<20:
                    i.append(-1)
            while len(filedata[today])<dt.now().hour:
                filedata[today].append([-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1])
            filedata[today].append([-1])
            while len(filedata[today][dt.now().hour])<int(dt.now().minute/3):
                filedata[today][dt.now().hour].append(-1)
        for i in filedata[today]:
            if filedata[today].index(i)==dt.now().hour:
                if len(i)<int(dt.now().minute/3):
                    for ii in range(int(dt.now().minute/3)-len(i)):
                        i.append(-1)
                break
            if len(i)<20:
                for ii in range(20-len(i)):
                    i.append(-1)
        file.seek(0)
        js.dump(filedata, file)
        file.close()

    data:list[int]=[]
    time:list[dt]=[]
    for i in range(20,24):
        for ii in range(20):
            try:
                point = filedata[(dt.now()-dtd(1)).strftime("%Y-%m-%d")][i][ii]
            except IndexError:
                point = -1
            # except 
            if point>10:
                data.append(point)
                time.append((dt.now()-dtd(1)).replace(hour=i,minute=ii*3))
    for i in range(min(dt.now().hour,14)):
        for ii in range(20):
            try:
                point = filedata[today][i][ii]
            except IndexError:
                point = -1
            if point>10:
                data.append(point)
                time.append((dt.now()).replace(hour=i,minute=ii*3))

    if not data:
        print("no data to process")
        return
    deriv=derivData(filterData(data[:]))

    minDeriv=min(deriv)
    toa = time[deriv.index(minDeriv)].strftime("%H:%M")   #time of arrival
    maxDeriv=max(deriv[deriv.index(minDeriv):])
    tod = time[deriv.index(maxDeriv)].strftime("%H:%M")   #time of departure
    tts = (time[deriv.index(maxDeriv)]-time[deriv.index(minDeriv)])    #total time slept

    conditions=[]
    conditions.append(tts>dtd(hours=4))
    conditions.append(minDeriv<-5000)
    conditions.append(minDeriv<-5000)
    conditions.append(minDeriv>-15000)
    conditions.append(maxDeriv>5000)
    conditions.append(maxDeriv<15000)
    validSleepPattern:bool = sum(conditions)==len(conditions)

    # print(time[deriv.index(min(deriv))])
    # print(time[deriv.index(max(deriv))])
    # print(tts)

    with open("slep_timestamps_data.json", "r+") as file:
        slepdata=js.load(file)
        if today in slepdata:
            if validSleepPattern:
                slepdata[today]=[toa,tod]
            else:
                slepdata[today]=[-1,-1]
        else:
            if validSleepPattern:
                slepdata.update({today:[toa,tod]})
            else:
                slepdata.update({today:[-1,-1]})
        file.seek(0)
        js.dump(slepdata, file)
        file.close()
    return

def provideData(client: socket):
    client.send(b"ok")
    #format: (string jour, int heure)
    date = client.recv(10).decode("utf-8")
    dateDelta = int.from_bytes(client.recv(1), "big")
    hourmin = int.from_bytes(client.recv(1), "big",signed=True)
    hourend = int.from_bytes(client.recv(1), "big",signed=True)
    print("{}, {} jours de {}h à {}h".format(date, dateDelta, hourmin, hourend))
    with open("slep_data.json", "r+") as file:
        data = js.load(file)
        file.close()
    try:
        for i in range(dateDelta):
            for ii in range(hourmin,hourend):
                if ii<0:
                    # print("{}, {}h".format(dt.strptime(date,"%Y-%m-%d")-dtd(i+1),24+ii))
                    for iii in data[(dt.strptime(date,"%Y-%m-%d")-dtd(i+1)).strftime("%Y-%m-%d")][24+ii]:
                        client.send(int.to_bytes(iii,4,"big",signed=True))
                else:
                    # print("{}, {}h".format(dt.strptime(date,"%Y-%m-%d")-dtd(i),ii))
                    for iii in data[(dt.strptime(date,"%Y-%m-%d")-dtd(i)).strftime("%Y-%m-%d")][ii]:
                        client.send(int.to_bytes(iii,4,"big",signed=True))
    except KeyError:
        client.send(b"keyerror")
        print("keyerror",sys.exc_info()[-1].tb_lineno)
        lookForErrors("keyerror")
    except IndexError:
        client.send(b"indexerror")
        print("indexerror",sys.exc_info()[-1].tb_lineno)
        lookForErrors("indexerror")
    client.close()

def provideTimestamps(client: socket.socket):
    print("providing slep stamps")
    client.send(b"ok")
    date:dt = dt.strptime(client.recv(10).decode("utf-8"),"%Y-%m-%d")
    dateDelta = int.from_bytes(client.recv(1), "big")
    with open("slep_timestamps_data.json", "r+") as file:
        slepdata:dict=js.load(file)
        file.close()
    i:str
    for i in range(dateDelta):
        try:
            if slepdata[(date-dtd(i)).strftime("%Y-%m-%d")][0]==-1:
                client.send(b"error")
                continue
            client.send(slepdata[(date-dtd(i)).strftime("%Y-%m-%d")][0].encode("utf-8"))
            client.send(slepdata[(date-dtd(i)).strftime("%Y-%m-%d")][1].encode("utf-8"))
        except KeyError:
            client.send(b"keyerror")
            print("keyerror",sys.exc_info()[-1].tb_lineno)
            lookForErrors("keyerror")
        except IndexError:
            client.send(b"indexerror")
            print("indexerror",sys.exc_info()[-1].tb_lineno)
            lookForErrors("indexerror")
    client.close()

def lookForErrors(name):
    global errors
    global errors_names
    errors+=1
    present = False
    for error_name in errors_names:
        if error_name == name:
            present = True
    if not present:
        errors_names.append(name)

s = socket.socket()         

s.bind(('0.0.0.0', 10000 ))
s.listen(0)
errors = 0
errors_names = [] 

init = threading.Thread(processData())
init.start()

while True:
    try:
        client, addr = s.accept()
        content = client.recv(32)
        client_name = client.getpeername()

        if content == b"slep":
            sleph = threading.Thread(saveData(client))
            sleph.start()
        
        if content == b"slep2":
            sleph = threading.Thread(saveData2(client))
            sleph.start()

        elif content == b"stop":
            client.send(b"ok")
            client.shutdown(socket.SHUT_RDWR)
            print("stop command recived from: ",client.getpeername())
            client.close()
            print("Stopping server")
            break

        elif content == b"ping":
            client.send(b"toe ta dlair dun ping")
            client.shutdown(socket.SHUT_RDWR)
            print("Ping command recived from: ",client.getpeername())
            client.close()

        elif content == b"slepdata":
            slepdh = threading.Thread(provideData(client))
            slepdh.start()

        elif content == b"slepstamps":
            slepdh = threading.Thread(provideTimestamps(client))
            slepdh.start()

        elif content == b"isThomInBed":
            itibh = threading.Thread(isThomInBed(client))
            itibh.start()

        else:
            command = content.decode("utf-8")
            print("unknown command (" + command + ") from: ")
            print(client_name)
            lookForErrors(command)
                    
    except TimeoutError:
        print("Client timed-out")
        lookForErrors("TimeoutError")
    except ConnectionResetError:
        print("Client badly closed socket")
        lookForErrors("ConnectionResetError")
    except Exception as exeption:
        erName = exeption.__class__.__name__
        print(erName,sys.exc_info()[-1].tb_lineno,exeption)
        lookForErrors(erName)

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