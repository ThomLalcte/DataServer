import pause
import datetime
import json
import socket
import threading

debugAlarm = datetime.datetime.now() + datetime.timedelta(minutes=2)

def getSchedule():
    with open('schedule.json') as f:
        schedule:dict = json.load(f)
    return schedule

def saveSchedule(schedule:dict):
    with open('schedule.json', 'w') as f:
        json.dump(schedule, f, indent=4)

def connectToMonitor():
    monitor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    monitor.connect(('192.168.0.150', 10001))
    return monitor

def getSensorReading(monitor:socket.socket = None):
    # get the current sensor reading
    disconnectFlag = False
    if monitor is None:
        monitor = connectToMonitor()
        disconnectFlag = True
    debug_message = monitor.recv(1024)
    monitor.send(b'gp')
    sensor_reading = monitor.recv(1024)
    sensor_reading = int(sensor_reading.decode('utf-8'))
    if disconnectFlag:
        monitor.close()        
    return sensor_reading

def get_next_alarm():
    # load the schedule
    schedule = getSchedule()

    # get the current time
    scanTime = datetime.datetime.now()

    # global debugAlarm
    # return debugAlarm

    while True:
        # get the current day of the week
        day = scanTime.strftime('%A').lower()

        # get the next alarm time
        next_alarm_from_json_iter = iter(list(schedule["alarms"]["weekdays"][day].keys()))
        
        for next_alarm_from_json in next_alarm_from_json_iter:
            # convert the next alarm time to a datetime object
            next_alarm_from_json_dt = datetime.datetime.strptime(next_alarm_from_json, '%H:%M')
            next_alarm = scanTime.replace(hour=next_alarm_from_json_dt.hour, minute=next_alarm_from_json_dt.minute, second=0, microsecond=0)

            if next_alarm > scanTime:
                return next_alarm
            
        # if we've reached this point, we've gone through all the alarms for the day
        # increment the day to midnight and try again
        scanTime = scanTime.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)

def updateSchedule(mean_reading_difference:float, inBedSensorReading:int):
    # wait 30 seconds to make get a stable sensor reading
    pause.until(datetime.datetime.now() + datetime.timedelta(minutes=5))
    # get the current sensor reading
    sensor_reading = getSensorReading()

    # update the rooster parameter
    schedule = getSchedule()
    # if sensor is too low, do not update the schedule
    if sensor_reading > schedule["stats"]["presence"]+mean_reading_difference/2:
        schedule["stats"]["absence"] = (schedule["stats"]["absence"]*2 + sensor_reading)/3
    if inBedSensorReading is not None:
        schedule["stats"]["presence"] = (schedule["stats"]["presence"]*2 + inBedSensorReading)/3
    saveSchedule(schedule)
    logActivity("schedule updated to {}".format(schedule))

def logActivity(activity:str, printFlag:bool = True):
    if printFlag:
        print(activity)
    with open('activity.log', 'a') as f:
        f.write('{}: {}\n'.format(datetime.datetime.now(), activity))

def enableAlarm():
    monitor = connectToMonitor()
    monitor.send(b'wu 1')
    monitor.close()
    logActivity('alarm enabled')

def disableAlarm():
    monitor = connectToMonitor()
    monitor.send(b'sa')
    monitor.close()
    logActivity('alarm disabled')


def main():

    # begin the loop
    inBedSensorReading:int = None # variable to hold the sensor reading when in bed until confirmed it's valid
    wakeParameterLabel = 'wake up (wu): '
    while True:
        # get the next alarm time
        next_alarm = get_next_alarm()
        print(next_alarm)

        # pause for 10 minutes or until the next alarm
        if datetime.datetime.now() + datetime.timedelta(minutes=10) > next_alarm:
            pause.until(next_alarm)


            # get the expected sensor reading from the schedule
            schedule = getSchedule()
            expected_sensor_reading = schedule["stats"]["presence"]
            mean_reading_difference = schedule["stats"]["absence"] - expected_sensor_reading
            logActivity('expected sensor reading: {}'.format(expected_sensor_reading))
            logActivity('mean reading difference: {}'.format(mean_reading_difference))

            # if the sensor reading is too high, do not activate the alarm
            sensor_reading = getSensorReading()
            logActivity('sensor reading: {}'.format(sensor_reading))
            if sensor_reading > expected_sensor_reading + mean_reading_difference/2:
                logActivity('sensor reading too high')
                continue
            
            # activate the alarm
            enableAlarm()
            
            next_alarm = get_next_alarm()
            logActivity('next alarm: {}'.format(next_alarm))

            outOfBed = False
            alarmStartTime = datetime.datetime.now()

            while not outOfBed:
                # get the debug message
                monitor = connectToMonitor()
                debug_message = monitor.recv(1024)
                monitor.close()
                
                # decode the answer
                debug_message = debug_message.decode('utf-8')
                # look for the wake up parameter in the debug message
                # find the index of the wake up parameter
                wake_up_index = debug_message.find(wakeParameterLabel)
                # read the string from the end of the wake up parameter to the next newline
                wake_up = debug_message[wake_up_index+len(wakeParameterLabel):].split('\n')[0]
                # print(wake_up)
                logActivity('alarm state: {}'.format(wake_up))

                if wake_up == 'false':
                    outOfBed = True
                    # update the schedule in a new thread to not block the alarm
                    threading.Thread(target=updateSchedule, args=(mean_reading_difference, inBedSensorReading)).start()
            
                    inBedSensorReading = None

                    # TODO: great spot to measure the time it takes to get out of bed

                # if the alarm has been going for more than 10 minute, stop it
                elif datetime.datetime.now() > alarmStartTime + datetime.timedelta(minutes=10):
                    # stop the alarm and break the loop
                    disableAlarm()
                    break

                else:
                    pause.until(datetime.datetime.now() + datetime.timedelta(seconds=10))
        
                                 
        elif datetime.datetime.now() + datetime.timedelta(minutes=21) > next_alarm:
            # get the mean reading difference between in/out of bed
            schedule = getSchedule()
            mean_reading_difference = schedule["stats"]["absence"] - schedule["stats"]["presence"]


            # get the current sensor reading
            sensor_reading = getSensorReading()
            logActivity("Alarm incoming soon - sensor reading: {}".format(sensor_reading))

            if sensor_reading < schedule["stats"]["presence"]+mean_reading_difference/2:
                inBedSensorReading = (inBedSensorReading*2 + sensor_reading)/3 if inBedSensorReading is not None else sensor_reading
                newPresenceThreshold = inBedSensorReading+mean_reading_difference*0.75
                monitor = connectToMonitor()
                monitor.send('mt {}'.format(newPresenceThreshold).encode('utf-8'))
                monitor.close()
                logActivity('presence threshold updated to {}'.format(newPresenceThreshold))


            # pause.until(datetime.datetime.now() + datetime.timedelta(seconds=10))
            pause.until(datetime.datetime.now() + datetime.timedelta(minutes=10))

        else:
            # pause.until(datetime.datetime.now() + datetime.timedelta(seconds=10))
            pause.until(datetime.datetime.now() + datetime.timedelta(minutes=10))
        



if __name__ == "__main__":
    main()