#!/usr/bin/env python3
import cayenne_credentials
import cayenne.client
import serial
from threading import Thread
import RPi.GPIO as GPIO
import time
from w1thermsensor import W1ThermSensor
import queue



levelSwitch = 3
sensor = W1ThermSensor()
range1 = 24
range2 = 25
range3 = 8
range4 = 7
relay1 = 6
relay2 = 13
relay3 = 19
relay4 = 26
sendQueue = queue.Queue()
station1Queue = queue.Queue()
station2Queue = queue.Queue()
station3Queue = queue.Queue()
station4Queue = queue.Queue()

global modeSelect
modeSelect = 1
global ozToPour
ozToPour = 2
global coolDownTime
coolDownTime =10
global pouredAmount
pouredAmount = 0

#gpio setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(levelSwitch, GPIO.IN)
GPIO.setup(range1, GPIO.IN)
GPIO.setup(range2, GPIO.IN)
GPIO.setup(range3, GPIO.IN)
GPIO.setup(range4, GPIO.IN)
GPIO.setup(relay1, GPIO.OUT)
GPIO.setup(relay2, GPIO.OUT)
GPIO.setup(relay3, GPIO.OUT)
GPIO.setup(relay4, GPIO.OUT)
uart_channel = serial.Serial("/dev/ttyS0", baudrate=115200, timeout =1)

def pouredAmountSend():
    global pouredAmount
    while True:
        value = "7,"+str(pouredAmount)+"\n"
        
        sendQueue.put(value)
        time.sleep(10)
        

class tempSensor:
    def __init__(self):
        self._running = True
    def run(self):
        while True:
            tempValue = sensor.get_temperature() *9 /5 +32
            sendValue = "3,"+str(tempValue) + "\n"
            sendQueue.put(sendValue)
            updateTemp(tempValue)
            time.sleep(10)
            
class waterSwtich:
    def __init__(self):
        self._running = True
    def run(self):
        while True:
            sendValue = ""
            if GPIO.input(levelSwitch):
                sendValue = "4,1\n"
            else:
                sendValue = "4,0\n"
            sendQueue.put(sendValue)
            time.sleep(10)

class txMsg:
    def __init__(self):
        self._running = True
    def run(self):
        while True:
            stringOut = sendQueue.get()
            sendQueue.task_done()
            print("tx: " + stringOut)
            bytesOut = stringOut.encode()
            uart_channel.write(bytesOut)

class rxMsg:
    def __init__(self):
        self._running = True
    def run(self):
        global modeSelect
        global ozToPour
        while True:
            dataChar = ""
            data = ""
            data1 =""
            while dataChar != "!":
                
                while uart_channel.inWaiting() < 1:
                    time.sleep(1)
                data = uart_channel.read(5)
                dataChar = data.decode("utf-8")
                #print("modeSel: " + str(modeSelect))
                #print("datachar: " + dataChar)
                if dataChar != "":
                    dataSplit = dataChar.split(",")
                    if dataSplit[0] == "0":
                            #mode
                        modeSelect = int(dataSplit[1])                            
                    elif dataSplit[0] == "1":
                            #pouramount
                        ozToPour = int(dataSplit[1])
                    elif dataSplit[0] == "2":
                                #start
                        if modeSelect == 1:
                            if dataSplit[1] == "1\n":
                                pourStation1 = Thread(target=pourStation, args=(1,))
                                pourStation1.start()
                            elif dataSplit[1] == "2\n":
                                pourStation2 = Thread(target=pourStation, args=(2,))
                                pourStation2.start()   
                            elif dataSplit[1] == "3\n":
                                pourStation3 = Thread(target=pourStation, args=(3,))
                                pourStation3.start()    
                            elif dataSplit[1] == "4\n":
                                pourStation4 = Thread(target=pourStation, args=(4,))
                                pourStation4.start()                                   
                                


                data = ""
                print("rx data: " + dataChar)
                uart_channel.flush
                time.sleep(1)

    
def stationRun(stationNumber):
    global ozToPour
    global coolDownTime
    global modeSelect
    if(stationNumber == 1):
        currentRange = 0
        while True:
            if modeSelect == 0:
                if not GPIO.input(range1):
                    print("holding for 2")
                    time.sleep(2)
                    if not GPIO.input(range1):
                        pourStation1 = Thread(target=pourStation, args=(1,))
                        pourStation1.start() 
    if(stationNumber == 2):
        currentRange = 0
        while True:
            if modeSelect == 0:
                if not GPIO.input(range2):
                    print("holding for 2")
                    time.sleep(2)
                    if not GPIO.input(range2):
                        pourStation2 = Thread(target=pourStation, args=(2,))
                        pourStation2.start()
                        
    if(stationNumber == 3):
        currentRange = 0
        while True:
            if modeSelect == 0:
                if not GPIO.input(range3):
                    print("holding for 2")
                    time.sleep(2)
                    if not GPIO.input(range3):
                        pourStation3 = Thread(target=pourStation, args=(3,))
                        pourStation3.start()
    if(stationNumber == 4):
        currentRange = 0
        while True:
            if modeSelect == 0:
                if not GPIO.input(range4):
                    print("holding for 2")
                    time.sleep(2)
                    if not GPIO.input(range4):
                        pourStation4= Thread(target=pourStation, args=(4,))
                        pourStation4.start() 

def pourStation(station):
    global coolDownTime
    global ozToPour
    msg = "6,"+str(station)+",2\n"
    sendQueue.put(msg)
    pourThread = Thread(target = pourTime, args=(station,ozToPour,))
    pourThread.start()
    pourThread.join()
    msg = "6,"+str(station)+",0\n"
    sendQueue.put(msg)
    time.sleep(coolDownTime)
    msg = "6,"+str(station)+",1\n"
    sendQueue.put(msg)
    print("made it")
                    
def pourTime(station, ozToPour):
    global pouredAmount
    if station == 1:
        GPIO.output(relay1, GPIO.HIGH)
        time.sleep(pourTimeTranslate(ozToPour))
        GPIO.output(relay1, GPIO.LOW)
        pouredAmount = pouredAmount + ozToPour
        updateOzPoured(1,ozToPour)
    if station == 2:
        GPIO.output(relay2, GPIO.HIGH)
        time.sleep(pourTimeTranslate(ozToPour))
        GPIO.output(relay2, GPIO.LOW)
        pouredAmount = pouredAmount + ozToPour
        updateOzPoured(2,ozToPour)
    if station == 3:
        GPIO.output(relay3, GPIO.HIGH)
        time.sleep(pourTimeTranslate(ozToPour))
        GPIO.output(relay3, GPIO.LOW)
        pouredAmount = pouredAmount + ozToPour
        updateOzPoured(3,ozToPour)
    if station == 4:
        GPIO.output(relay4, GPIO.HIGH)
        time.sleep(pourTimeTranslate(ozToPour))
        GPIO.output(relay4, GPIO.LOW)
        pouredAmount = pouredAmount + ozToPour
        updateOzPoured(4,ozToPour)
        
def pourTimeTranslate(ozToPour):
    #3sec = 100 mL
    if ozToPour == 2:
        return 1.6
    if ozToPour == 6:
        return 5
    if ozToPour == 10:
        return 8.3
    if ozToPour == 12:
        return 10
    if ozToPour == 16:
        return 13.4

def updateOzPoured(station, ozPoured):
    global cayenne_client
    global ozPouredStation1
    global ozPouredStation2
    global ozPouredStation3
    global ozPouredStation4
    if (1 == station):
        ozPouredStation1 += int(ozPoured)
        cayenne_client.virtualWrite(
                int(station), int(ozPouredStation1), dataType="liquid", dataUnit="oz")
    
    elif (2 == station):
        ozPouredStation2 += int(ozPoured)
        cayenne_client.virtualWrite(
                int(station), int(ozPouredStation2), dataType="liquid", dataUnit="oz")
        
    elif (3 == station):
        ozPouredStation3 += int(ozPoured)
        cayenne_client.virtualWrite(
                int(station), int(ozPouredStation3), dataType="liquid", dataUnit="oz")
        
    elif (4 == station):
        ozPouredStation4 += int(ozPoured)
        cayenne_client.virtualWrite(
                int(station), int(ozPouredStation4), dataType="liquid", dataUnit="oz")
        
    else:
        pass

def updateTemp(temp: float):
    global cayenne_client
    cayenne_client.virtualWrite(
                cayenne_credentials.VIRTUAL_CHANNEL.TEMPERATURE.value, float(temp), dataType="temp", dataUnit="f")

def mqtt_loop():
    global cayenne_client
    while (True):
        time.sleep(cayenne_credentials.MQTT_LOOP_TIME_SECONDS)
        cayenne_client.loop()

cayenne_client = cayenne.client.CayenneMQTTClient()
cayenne_client.begin(str(cayenne_credentials.MQTT_USERNAME),
                                str(cayenne_credentials.MQTT_PASSWORD), str(cayenne_credentials.CLIENT_ID), port=int(cayenne_credentials.MQTT_PORT))

ozPouredStation1 = 0
ozPouredStation2 = 0
ozPouredStation3 = 0
ozPouredStation4 = 0

temperSensor = tempSensor()
tempThread = (Thread(target=temperSensor.run))
tempThread.start()
              
levelSensor = waterSwtich()
sensorThread = Thread(target=levelSensor.run)
sensorThread.start()

rxUart = rxMsg()
rxThread = Thread(target=rxUart.run)
rxThread.start()

txUart = txMsg()
txThread = Thread(target=txUart.run)
txThread.start()

amountThread = Thread(target = pouredAmountSend)
amountThread.start()

station1Thread = Thread(target=stationRun, args=(1,))
station1Thread.start()
station2Thread = Thread(target=stationRun, args=(2,))
station2Thread.start()
station3Thread = Thread(target=stationRun, args=(3,))
station3Thread.start()
station4Thread = Thread(target=stationRun, args=(4,))
station4Thread.start()
mqtt_service_thread = Thread(target=mqtt_loop)
mqtt_service_thread.start()

data1 = " "
data = " "
while 1:
    #print(GPIO.input(levelSwitch))
    #print(modeSelect)
    
    time.sleep(3 )
