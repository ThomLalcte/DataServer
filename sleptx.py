import json as js
from datetime import datetime as dt
import time 
#import requests as rq
import matplotlib.pyplot as plt
import numpy as np
import calendar as cal
import socket

span = 12
interval = 5

print("I EAT GARBAGE")

s = socket.socket()         
 
s.bind(('0.0.0.0', 10000 ))
s.listen(0)    

r = 0

while True:

    print(dt.now())
    client, addr = s.accept()
 
    while True:
        content = client.recv(32)
 
        if len(content) == 0:
           break
 
        else:
            r = content
            print(r)
 
    print("Closing connection")
    client.close()

    with open("data.json", "r+") as file:
        today = str(dt.now().year) + "-" + str(dt.now().month) + "-" + str(dt.now().day)
        
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

        if dt.now().minute%10 < 5:
            x = []
            y = []
            top = 0
            
            xm = [0]

            if dt.now().hour-span >= 0: #cas où l'interval est compris dans la journée actuelle
                if dt.now().hour > len(data[str(dt.now().year) + "-" + str(dt.now().month) + "-" + str(dt.now().day)]):
                    print("Error: insuffiscient hour data to process")

                else:
                    for i in range(dt.now().hour-span,dt.now().hour):
                        g = 0.0 #pour la graduation

                        for key in data[str(dt.now().year) + "-" + str(dt.now().month) + "-" + str(dt.now().day)][i]: #iteration des tranches de 5 min de l'heure i
                            x.append(key)
                            y.append(i+g)
                            g+=interval/60.0
                            top = max(top,key) #calcul de la valeur max pour le posistionnement de la moyenne de mouvement/interval

                            #intégration de x
                            xm.append(xm[-1]+key)

            
            if dt.now().hour-span < 0:#cas où l'interval est compris entre aujourd'hui et hier

                jouraregarder = str(dt.now().year) + "-" + str(dt.now().month) + "-" + str(dt.now().day-1)
                if dt.now().day-1 == 0: #cas où le jour précédent est dans un autre mois
                    wkd, nday = cal.monthrange(dt.now().year,dt.now().month-1)
                    jouraregarder = str(dt.now().year) + "-" + str(dt.now().month-1) + "-" + str(nday)

                if dt.now().hour > len(data[str(dt.now().year) + "-" + str(dt.now().month) + "-" + str(dt.now().day)]):
                    print("Error: insuffiscient hour data to process")

                elif not jouraregarder in data:
                    print("Error: no previous day data to process")
                    
                elif 23 > len(data[jouraregarder]):
                    print("Error: insuffiscient previous day's hour data to process")

                else: 
                    for i in range(23+dt.now().hour-span,23):
                        g = 0.0 #pour la graduation

                        for key in data[jouraregarder][i]: #iteration des tranches de 5 min de l'heure i
                            x.append(key)
                            y.append(i-23.0+g)
                            g+=interval/60.0
                            top = max(top,key) #calcul de la valeur max pour le posistionnement de la moyenne de mouvement/interval

                            #intégration de x
                            xm.append(xm[-1]+key)

                    for i in range(0,dt.now().hour):
                        g = 0.0 #pour la graduation

                        if i >= len(data[str(dt.now().year) + "-" + str(dt.now().month) + "-" + str(dt.now().day)]):
                            print("Error: insuffiscient hour data to process")
                            break

                        for key in data[str(dt.now().year) + "-" + str(dt.now().month) + "-" + str(dt.now().day)][i]: #iteration des tranches de 5 min de l'heure i
                            x.append(key)
                            y.append(i+g)
                            g+=interval/60.0
                            top = max(top,key) #calcul de la valeur max pour le posistionnement de la moyenne de mouvement/interval

                            #intégration de x
                            xm.append(xm[-1]+key)
            plt.annotate(round(xm[-1]/216,3), xy=(dt.now().hour-span/2-2, 3*top/4)) #affichage de la moyenne de mouvement/interval
            plt.plot(y,x)
            plt.savefig("C:\inetpub\wwwroot\yabro.png",dpi=500)
            plt.clf()

            if dt.now().hour == 12 and dt.now().minute < 60: #sauvegarde des stats
                if not "tots" in data:
                    data.update({"tots":[]})
                data["tots"].append(xm[-1]) #sauvegarde des totaux/jours
                #data["slep_jour"].append(round(y[xdd.index(max(xdd))]-y[xdd.index(min(xdd))],2)) #sauvegarde des heures de sommeils/jours
                data.pop(str(dt.now().year) + "-" + str(dt.now().month) + "-" + str(dt.now().day-2),None) #effacage des données entérieures
                plt.plot(data["tots"])
                plt.savefig("C:\inetpub\wwwroot\\tots.png",dpi=500) 
                plt.clf()

                jouraregarder = str(dt.now().year) + "-" + str(dt.now().month) + "-" + str(dt.now().day-2)
                if dt.now().day-2 <= 0: #cas où le jour précédent est dans un autre mois
                    wkd, nday = cal.monthrange(dt.now().year,dt.now().month-1)
                    jouraregarder = str(dt.now().year) + "-" + str(dt.now().month-1) + "-" + str(nday+dt.now().day-2)

                if jouraregarder in data:
                    data.pop(jouraregarder) #enlevage des données superflues


        
