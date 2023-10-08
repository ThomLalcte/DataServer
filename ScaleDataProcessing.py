import numpy as np
import os
import matplotlib.pyplot as plt
import datetime as dt

def main():

    dataDir = "Z:/dataServer/data/scale"
    cutoff = 8.5e5
    data:dict[str, np.ndarray] = {}
    batteryLevel:list = [[],[]]
    weightThom:list = [[],[]]
    weightEmy:list = [[],[]]
    cal:list = [[],[]]
    refThom:list = [[227.6,227.6],[dt.datetime(2023,5,14,20,39,0),dt.datetime(2023,5,20,20,23,0)]]
    refEmy:list = [[123.8],[dt.datetime(2023,5,20,20,23,0)]]
    calParam:list = [5.96586E-11,1.24984E-04,1.87317E+01]
    # calParam:list = [3.5420e-11,-1.5958e-04,-27.257]

    
    # Load csv data
    files = os.listdir(dataDir)
    # sort the files by date from lastest to oldest
    files.sort(key=lambda x: dt.datetime.strptime(x[:-4], '%Y-%m-%d_%H-%M-%S'), reverse=True)

    for file in files:
        if file.endswith(".csv"):
            measurement = np.loadtxt(dataDir + "/" + file, delimiter=',', dtype=np.float32)
            data.update({file: measurement[3:]})
            batteryLevel[0].append(measurement[1])
            batteryLevel[1].append(dt.datetime.strptime(file[:-4], '%Y-%m-%d_%H-%M-%S'))
        
        mean = np.mean(measurement[3:])
        std = np.std(measurement[3:])

        if std > 30000:
            cal[0].append(np.mean(measurement[3:30]))
            cal[1].append(dt.datetime.strptime(file[:-4], '%Y-%m-%d_%H-%M-%S'))
            # display the measurement
            plt.plot(measurement[3:]-cal[0][-1])
            plt.title(file)

            sampleTime = dt.datetime.strptime(file[:-4], '%Y-%m-%d_%H-%M-%S')
            # calcultate the weight of only the lowest values
            # first get the std of valid values
            stdTop = np.std(measurement[3:][measurement[3:]-cal[0][-1] < mean+std/5])

            # get the mean of smaller values than mean+std/5
            # sample = np.abs(np.mean(measurement[measurement < mean+std/5][5:-5])-cal[0][-1])
            sample = np.abs(np.mean(measurement[measurement < measurement[3:].min()+stdTop/2])-cal[0][-1])

            # plt.hlines(measurement[3:].min()+stdTop-cal[0][-1], 0 , len(measurement[3:]))
            # plt.hlines(mean+std/5, 0 , len(measurement[3:]))
            plt.show()
            if sample < cutoff:
                weightEmy[0].append(sample)
                weightEmy[1].append(sampleTime)
            else:
                weightThom[0].append(np.abs(np.mean(measurement[measurement < mean+std/5])-cal[0][-1]))
                weightThom[1].append(sampleTime)
    
    # find the closest scale measurement for each cal value timewise
    refThom.append([])
    for i in range(len(refThom[1])):
        timeDiff = []
        for j in range(len(weightThom[1])):
            timeDiff.append(np.abs((refThom[1][i]-weightThom[1][j]).total_seconds()))
        refThom[2].append(weightThom[1][np.argmin(timeDiff)])
    
    refEmy.append([])
    for i in range(len(refEmy[1])):
        timeDiff = []
        for j in range(len(weightEmy[1])):
            timeDiff.append(np.abs((refEmy[1][i]-weightEmy[1][j]).total_seconds()))
        refEmy[2].append(weightEmy[1][np.argmin(timeDiff)])

    # print the mean calibration value
    print(np.mean(cal[0]))

    # convert lsb to lbs
    weightThom.append([])
    for weight in range(len(weightThom[0])):
        # # find the closest ref value for each weight measurement timewise
        # # use this if the scale is not calibrated
        # timeDiff = []
        # for i in range(len(refThom[1])):
        #     timeDiff.append(np.abs(weightThom[1][weight]-refThom[1][i]))
        # idx = np.argmin(timeDiff)
        # # convert lsb to lbs
        # weightThom[2].append((weightThom[0][weight]*refThom[0][idx]/weightThom[0][idx]))
        print(f"{weightThom[1][weight]}\t{weightThom[0][weight]}")
        weightThom[2].append(weightThom[0][weight]**2*calParam[0]+weightThom[0][weight]*calParam[1]+calParam[2])
    
    # convert lsb to lbs
    weightEmy.append([])
    for weight in range(len(weightEmy[0])):
        # find the closest ref value for each weight measurement timewise
        # timeDiff = []
        # for i in range(len(refEmy[1])):
        #     timeDiff.append(np.abs(weightEmy[1][weight]-refEmy[1][i]))
        # idx = np.argmin(timeDiff)
        # # convert lsb to lbs
        # weightEmy[2].append(weightEmy[0][weight]*refEmy[0][idx]/weightEmy[0][idx])
        print(f"{weightEmy[1][weight]}\t{weightEmy[0][weight]}")
        weightEmy[2].append(weightEmy[0][weight]**2*calParam[0]+weightEmy[0][weight]*calParam[1]+calParam[2])

    # save the reference values
    # use to calculate the calibration parameters
    # np.savetxt("refThom.csv", refThom, delimiter=',', fmt='%s')
    # np.savetxt("refEmy.csv", refEmy, delimiter=',', fmt='%s')

    # plt.plot(batteryLevel[1], batteryLevel[0], '-o')
    # plt.title("Battery Level")
    # plt.figure()
    plt.plot(weightEmy[1], weightEmy[2], '-o')
    plt.title("Weight")
    plt.twinx()
    plt.plot(weightThom[1], weightThom[2], '-o', color='green')
    # plt.title("Weight Thom")
    # plt.figure()
    # plt.plot(cal[1], cal[0], '-o')
    # plt.title("Calibration")
    plt.show()


if __name__ == '__main__':
    main()