import json as js
from datetime import datetime as dt

import matplotlib.pyplot as plt
import calendar as cal

span = 6        #étendue du graphique
x = []
y = []
today = str(dt.now().year) + "-" + str(dt.now().month) + "-" + str(dt.now().day)
today = "2021-5-25"
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
            print(gg)
            for key in data[today][i]: #iteration des tranches de 5 min de l'heure i
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
plt.show()
#plt.savefig("yabro.png",dpi=250)
#plt.savefig("C:\inetpub\wwwroot\yabro.png",dpi=250)
plt.clf()