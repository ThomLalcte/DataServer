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

def saveData(client: socket):
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
                    data[today].append([-1])
                data[today].append([int(r)])
        else:
            data.update({today:[[int(r)]]})

        file.seek(0)
        js.dump(data, file)
        file.close()
    if dt.now().minute%30<2:
        processData()
    return

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

def isThomInBed(client: socket):
    client.send(b"ok")
    client.send(int.to_bytes(slepLastSample<threshold,1,"big"))
    print("itib call from {}".format(client.getpeername()))
    client.close()

def processData():
    with open("slep_data.json", "r+") as file:
        filedata = js.load(file)
        mean=filedata[dt.now().strftime("%Y-%m-%d")][9][1]+filedata[dt.now().strftime("%Y-%m-%d")][9][2]
        filedata[dt.now().strftime("%Y-%m-%d")][9][1:3]=[int(mean/2), int(mean/2)]
        file.seek(0)
        js.dump(filedata, file)
        file.close()

    data=[]
    time=[]
    for i in range(20,24):
        for ii in range(0,20):
            try:
                point = filedata[(dt.now()-dtd(1)).strftime("%Y-%m-%d")][i][ii]
            except IndexError:
                point = -1
            if point ==-1:
                return
            data.append(point)
            time.append((dt.now()-dtd(1)).replace(hour=i,minute=ii*3))
    for i in range(0,dt.now().hour):
        for ii in range(0,20):
            point = filedata[dt.now().strftime("%Y-%m-%d")][i][ii]
            if point ==-1:
                return
            data.append(point)
            time.append((dt.now()).replace(hour=i,minute=ii*3))

    deriv=derivData(filterData(data[:]))

    # plt.plot(time,data)
    # plt.plot(time,filteredData)
    # plt.plot(time,deriv)
    # plt.gca().xaxis.set_major_formatter(pltd.DateFormatter('%H:%M'))
    # plt.show()

    toa = time[deriv.index(min(deriv))].strftime("%H:%M")   #time of arrival
    tod = time[deriv.index(max(deriv))].strftime("%H:%M")   #time of departure
    #tts = (time[deriv.index(max(deriv))]-time[deriv.index(min(deriv))])    #total time slept

    with open("slep_timestamps_data.json", "r+") as file:
        slepdata=js.load(file)
        today = dt.now().strftime("%Y-%m-%d")
        if today in slepdata:
            if max(abs(min(deriv)),abs(max(deriv)))<1000:
                slepdata[today]=[-1,-1]
            else:
                slepdata[today]=[toa,tod]
        else:
            if max(abs(min(deriv)),abs(max(deriv)))<1000:
                slepdata.update({today:[-1,-1]})
            else:
                slepdata.update({today:[toa,tod]})
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
                    print("{}, {}h".format(dt.strptime(date,"%Y-%m-%d")-dtd(i+1),24+ii))
                    for iii in data[(dt.strptime(date,"%Y-%m-%d")-dtd(i+1)).strftime("%Y-%m-%d")][24+ii]:
                        client.send(int.to_bytes(iii,4,"big",signed=True))
                else:
                    print("{}, {}h".format(dt.strptime(date,"%Y-%m-%d")-dtd(i),ii))
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

def provideTimestamps(client: socket):
    pass

def lookForErrors(name):
    global errors
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


processData()

while True:
    try:
        client, addr = s.accept()
        content = client.recv(32)
        client_name = client.getpeername()

        if content == b"slep":
            sleph = threading.Thread(saveData(client))
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
    # except Exception as exeption:
    #     erName = exeption.__class__.__name__
    #     print(erName,sys.exc_info()[-1].tb_lineno,exeption)
    #     lookForErrors(erName)

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