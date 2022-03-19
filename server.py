import threading
import socket
import sys
import json as js
from datetime import datetime as dt
from datetime import timedelta as dtd
from matplotlib import pyplot as plt
import matplotlib.dates as pltd
import struct
import os

meanHighValue = 1276000
meanLowValue = 1160574
threshold =meanLowValue+(meanHighValue-meanLowValue)/2
capLastSample=0
lastBootTime=dt.now()
wake:int=0

print(os.path.dirname(os.path.abspath(__file__)))
print(os.path.abspath(os.getcwd()))

def AppendDatatoFile(fileName:str,data):
    hour=dt.now().hour.__str__()
    try:
        with open(fileName, "r+") as file:
            filedata = js.load(file)
            file.close()
    except FileNotFoundError:
        filedata={}
    if hour in filedata.keys():
        filedata[hour].append(data)
    else:
        filedata.update({hour:[data]})
    with open(fileName, "w") as file:
        js.dump(filedata, file)
        file.close()

def loadFromFile(dataType,date:dt,dateDelta:int):
    filedata:dict={}
    for i in range(dateDelta+1):
        day = (date-dtd(i)).strftime("%Y-%m-%d")
        filedata.update({day:{}})
        if dataType==b"capp" or dataType=="capp":
            filename="data/cap/"+day+".json"
        
        if dataType==b"wigg" or dataType=="wigg":
            filename="data/wiggle/"+day+".json"

        if dataType==b"temp" or dataType=="temp":
            filename="data/temp/"+day+".json"
        
        if dataType==b"ligt" or dataType=="ligt":
            filename="data/light/"+day+".json"
            
        try:
            with open(filename, "r") as file:
                filedata[day].update(js.load(file))
                file.close()
        except FileNotFoundError:
            continue
    return filedata

def HandleSlepClient(client: socket.socket):
    interval = 3
    buffer=b""
    eta=(interval-dt.now().minute%interval)*60-dt.now().second
    if eta<interval/2*60:
        eta+=interval*60
    buffer+=wake.to_bytes(2,"big",signed=False)
    buffer+=eta.to_bytes(2,"big",signed=False)
    client.send(buffer)
    slepQte = client.recv(4)
    wiggleQte = client.recv(4)
    # tempRaw = client.recv(4)
    lightQte = client.recv(2)
    client.close()
    c = int.from_bytes(slepQte, "big")
    w = int.from_bytes(wiggleQte, "big")
    # t = int.from_bytes(tempRaw, "big")
    l = int.from_bytes(lightQte, "big")
    print("slep repport: ",c)
    print("wiggle repport: ",w)
    # print("temperature repport: ",t*0.0078125)
    print("light repport: ",l)
    global capLastSample
    capLastSample = c
    today = dt.now().strftime("%Y-%m-%d")
    AppendDatatoFile("data/wiggle/"+today+".json",w)
    AppendDatatoFile("data/cap/"+today+".json",c)
    # AppendDatatoFile("data/temp/"+today+".json",t)
    AppendDatatoFile("data/light/"+today+".json",l)

    if dt.now().minute%30<2:
        processData(dt.now(),"capp")

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
    client.send(int.to_bytes(capLastSample<threshold,1,"big"))
    print("itib call from {}".format(client.getpeername()))
    client.close()

def processData(date:dt,dataType:str):
    datestr = date.strftime("%Y-%m-%d")
    filedata = loadFromFile(dataType,date,1)
    #file->dict object for analysis
    data:list[int]=[]
    time:list[dt]=[]
    for ii in range(-4,min(date.hour+1,14)):#on itère les heures demandées
        day = (date-dtd(ii<0)).strftime("%Y-%m-%d")#contien la journée corrigé pour les heures négative (-1 jour)
        if not day in filedata.keys() or not str(ii) in filedata[day].keys():#si le jour ou l'heure est pas listé on envoie des -1
            for iii in range(20):
                data.append(-1)
                time.append((date-dtd(ii<0)).replace(hour=ii+24*(ii<0),minute=iii*3))
            continue
        hour = str(ii+24*(ii<0))#contient heure corrigée pour heures négatives
        lenii=min(len(filedata[day][hour]),20)
        for iii in range(lenii):#envoi les minutes qui existent
            data.append(filedata[day][hour][iii])
            time.append((date-dtd(ii<0)).replace(hour=ii+24*(ii<0),minute=iii*3))
        for iii in range(20-lenii):#envoi de -1 pour ceux qui exisntent pas
            data.append(-1)
            time.append((date-dtd(ii<0)).replace(hour=ii+24*(ii<0),minute=(iii+lenii)*3))

    # plt.plot(time,data)
    # plt.gca().xaxis.set_major_formatter(pltd.DateFormatter('%H:%M'))
    # plt.legend()
    # plt.show()
    deriv=derivData(filterData(data[:]))
    minDeriv=min(deriv)
    i=deriv.index(minDeriv)
    while minDeriv<-20000:
        minDeriv=min(deriv[i:])
        i=min(deriv.index(minDeriv)+10,len(deriv)-1)
    toa = time[i].strftime("%H:%M")   #time of arrival
    maxDeriv=max(deriv[i:])
    while maxDeriv>15000:
        maxDeriv=max(deriv[i:])
        i=min(deriv.index(maxDeriv)+10,len(deriv)-1)
    tod = time[deriv.index(maxDeriv)].strftime("%H:%M")   #time of departure
    tts = (time[deriv.index(maxDeriv)]-time[deriv.index(minDeriv)])    #total time slept

    conditions=[]
    conditions.append(tts>dtd(hours=4))
    conditions.append(minDeriv<-5000)
    conditions.append(minDeriv>-20000)
    conditions.append(maxDeriv>5000)
    conditions.append(maxDeriv<15000)
    validSleepPattern:bool = sum(conditions)==len(conditions)

    onlyValidSamples=-1!=min(data[:])

    with open("data/slep_timestamps_data.json", "r") as file:
        slepdata=js.load(file)
        file.close()
    if datestr in slepdata:
        if validSleepPattern:
            slepdata[datestr]=[toa,tod]
        elif not onlyValidSamples:
            slepdata[datestr]=[-1]
        else:
            slepdata[datestr]=conditions
    else:
        if validSleepPattern:
            slepdata.update({datestr:[toa,tod]})
        elif not onlyValidSamples:
            slepdata.update({datestr:[-1]})
        else:
            slepdata.update({datestr:conditions})
    with open("data/slep_timestamps_data.json", "w") as file:
        file.seek(0)
        js.dump(slepdata, file)
        file.close()

def provideData(client: socket.socket):
    client.send(b"ok")
    datatype:bytes = client.recv(4)
    
    #format: (string jour, int heure)
    date = client.recv(10).decode("utf-8")
    datedt = dt.strptime(date,"%Y-%m-%d")
    dateDelta = int.from_bytes(client.recv(1), "big")
    hourmin = int.from_bytes(client.recv(1), "big",signed=True)
    hourend = int.from_bytes(client.recv(1), "big",signed=True)
    
    print("{}, {}, {} jours de {}h à {}h".format(datatype, date, dateDelta, hourmin, hourend))    
    
    filedata = loadFromFile(datatype,datedt,dateDelta+(hourmin<0))

    for i in range(dateDelta):#on itère les dates demandeés
        for ii in range(hourmin,hourend):#on itère les heures demandées
            day = (datedt-dtd(i+(ii<0))).strftime("%Y-%m-%d")#contien la journée corrigé pour les heures négative (-1 jour)
            if not day in filedata.keys() or not str(ii+24*(ii<0)) in filedata[day].keys():#si le jour ou l'heure est pas listé on envoie des -1
                for iii in range(20):
                    client.send(int.to_bytes(-1,4,"big",signed=True))
                continue
            hour = str(ii+24*(ii<0))#contient heure corrigée pour heures négatives
            for iii in filedata[day][hour]:#envoi les minutes qui existent
                client.send(int.to_bytes(iii,4,"big",signed=True))
            for iii in range(20-len(filedata[day][hour])):#envoi de -1 pour ceux qui exisntent pas
                client.send(int.to_bytes(-1,4,"big",signed=True))
    client.close()

def provideTimestamps(client: socket.socket):
    print("providing slep stamps")
    client.send(b"ok")
    date:dt = dt.strptime(client.recv(10).decode("utf-8"),"%Y-%m-%d")
    dateDelta = int.from_bytes(client.recv(1), "big")
    with open("slep_timestamps_data.json", "r") as file:
        slepdata:dict=js.load(file)
        file.close()
    i:str
    for i in range(dateDelta):
        try:
            sample:list = slepdata[(date-dtd(i)).strftime("%Y-%m-%d")]
            if sample[0]==-1:
                client.send(b"error")
                continue
            if len(sample)!=2:
                client.send(b"inslp")
                continue
            client.send(sample[0].encode("utf-8"))
            client.send(sample[1].encode("utf-8"))
        except KeyError:
            client.send(b"keyer")
            print("keyerror",sys.exc_info()[-1].tb_lineno)
            lookForErrors("keyerror")
        except IndexError:
            client.send(b"inder")
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

def repairData(date:dt=dt.today(), filename:str="data/cap_data.json"):
    datestr = date.strftime("%Y-%m-%d")
    previous = (date-dtd(1)).strftime("%Y-%m-%d")
    with open(filename, "r") as file:
        filedata:dict = js.load(file)
        file.close()
    # tapon de code qui sert à réparer les données. Jespère que t content que je l'ai fait pour toi
    # if (date.hour==10):
    #     mean=filedata[datestr][9][1]+filedata[datestr][9][2]
    #     filedata[datestr][9][1:3]=[int(mean/2), int(mean/2)]
    if not previous in filedata:
        fill = []
        for i in range(date.hour):
            fill+=[[-1]]
            # fill+=[[-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]]
        filedata.update({previous:fill})
    if not datestr in filedata:
        fill = []
        for i in range(date.hour):
            fill+=[[-1]]
            # fill+=[[-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]]
        filedata.update({datestr:fill})
    if len(filedata[previous])<24:
        # for i in filedata[previous]:
        #     while len(i)<20:
        #         i.append(-1)
        while len(filedata[previous])<24:
            filedata[previous].append([-1])
            # filedata[previous].append([-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1])
    # for i in filedata[previous]:
    #     if len(i)<20:
    #         for ii in range(20-len(i)):
    #             i.append(-1)
    if len(filedata[datestr])<date.hour+1:
        for i in filedata[datestr]:
            while len(i)<20:
                i.append(-1)
        while len(filedata[datestr])<date.hour:
            filedata[datestr].append([-1])
            # filedata[datestr].append([-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1])
        filedata[datestr].append([-1])
        while len(filedata[datestr][date.hour])<int(date.minute/3):
            filedata[datestr][date.hour].append(-1)
    for i in filedata[datestr]:
        if filedata[datestr].index(i)==date.hour:
            if len(i)<int(date.minute/3):
                for ii in range(int(date.minute/3)-len(i)):
                    i.append(-1)
            break
        if len(i)<20:
            for ii in range(20-len(i)):
                i.append(-1)
    with open(filename, "w") as file:
        js.dump(filedata, file)
        file.close()

def repairBootGlitch():
    datestr = dt.today().strftime("%Y-%m-%d")
    if lastBootTime-dt.now()>dtd(minutes=10):
        return
    with open("cap_data.json", "r") as file:
        filedata:dict = js.load(file)
        file.close()
    summ = 0
    try:
        filedata[datestr][-1][-3:]=filterData(filedata[datestr][-1][-3:])
    except Exception as ex:
        print("repairBootGlitch a chié")
        erName = ex.__class__.__name__
        print(erName,sys.exc_info()[-1].tb_lineno,ex)
        lookForErrors(erName)
    

s = socket.socket()         
s.bind(('0.0.0.0', 10000 ))
s.listen(0)
errors = 0
errors_names = [] 

proh = threading.Thread(processData(dt.now(),"capp"))
proh.start()
print("--------------------------------------")
print("boot time: "+dt.now().strftime("%a %m-%d-%H:%M"))

while True:
    try:
        client, addr = s.accept()
        content = client.recv(32)
        client_name = client.getpeername()

        if content == b"slep":
            sleph = threading.Thread(HandleSlepClient(client))
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

        elif content == b"data":
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
        print("---------Error Occured---------")
        print(erName,sys.exc_info()[-1].tb_lineno,exeption)
        lookForErrors(erName)

#server logs
if errors>0:
    with open("data/server_log_data.json", "r") as file:
        data = js.load(file)
        file.close()
    today = str(dt.now().year) + "-" + str(dt.now().month) + "-" + str(dt.now().day)
    data.update({today:[errors,errors_names]})
    with open("data/server_log_data.json", "w") as file:
        js.dump(data, file)
        file.close()

print("--------------------------------------")
print("shutdown time: "+dt.now().strftime("%a %m-%d-%H:%M"))
