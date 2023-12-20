import sys
import traceback
from datetime import datetime

import u3
import u6
import ue9


# MAX_REQUESTS is the number of packets to be read.
MAX_REQUESTS = 75
# SCAN_FREQUENCY is the scan frequency of stream mode in Hz
SCAN_FREQUENCY = 100
SURGE_MIN = -5 #Вольты
SURGE_MAX= 5 #Вольты
SWAY_MIN = -5 #Вольты
SWAY_MAX= 5 #Вольты
YAW_MIN = -5 #Вольты
YAW_MAX= 5 #Вольты
HEAVY_MIN = -1 #Вольты
HEAVY_MAX= 1 #Вольты




d = None

d = ue9.UE9(ethernet=True, ipAddress="172.27.12.71")

# For applying the proper calibration to readings.
d.getCalibrationData()

print("Configuring UE9 stream")

d.streamConfig(NumChannels=4, 
               ChannelNumbers=[0, 1, 2, 3], 
               ChannelOptions=[8, 8, 8, 8], 
               SettlingTime=0, 
               Resolution=12, 
               ScanFrequency=SCAN_FREQUENCY)


try:
    print("Start stream")
    d.streamStart()
    start = datetime.now()
    print("Start time is %s" % start)

    missed = 0
    dataCount = 0
    packetCount = 0

    for r in d.streamData():
        
        if r is not None:
            # Our stop condition
            #if dataCount >= MAX_REQUESTS:
            #    break
           # print(r)
           # continue 
        
            if r["errors"] != 0:
                print("Errors counted: %s ; %s" % (r["errors"], datetime.now()))

            if r["numPackets"] != d.packetsPerRequest:
                print("----- UNDERFLOW : %s ; %s" %
                      (r["numPackets"], datetime.now()))

            if r["missed"] != 0:
                missed += r['missed']
                print("+++ Missed %s" % r["missed"])

            # Comment out these prints and do something with r
            #print("Average of %s AIN0, %s AIN1 readings: %s, %s" %
            #      (len(r["AIN0"]), len(r["AIN1"]), 
            #       sum(r["AIN0"])/len(r["AIN0"]), 
            #       sum(r["AIN1"])/len(r["AIN1"])))
            
            surge_len = len(r["AIN0"]) 
            sway_len = len(r["AIN1"])
            yaw_len = len(r["AIN2"])
            heavy_len = len(r["AIN3"])
        
            surge_val = sum(r["AIN0"])/len(r["AIN0"]) 
            sway_val = sum(r["AIN1"])/len(r["AIN1"])
            yaw_val = sum(r["AIN2"])/len(r["AIN2"])
            heavy_val = sum(r["AIN3"])/len(r["AIN3"])
            
            surge_valnorm = ((surge_val - SURGE_MIN)/(SURGE_MAX - SURGE_MIN))*400
            sway_valnorm = ((sway_val - SWAY_MIN)/(SWAY_MAX - SWAY_MIN))*400
            yaw_valnorm = ((yaw_val - YAW_MIN)/(YAW_MAX - YAW_MIN))*400
            heavy_valnorm = ((heavy_val - HEAVY_MIN)/(HEAVY_MAX - HEAVY_MIN))*400
            
            integer_surge_valnorm = int(surge_valnorm)
            integer_sway_valnorm = int(sway_valnorm)
            integer_yaw_valnorm = int(yaw_valnorm)
            integer_heavy_valnorm = int(heavy_valnorm)
            #print(f"SURGE:\tAVERAGE: {surge_len}\tREADINGS: {surge_val}")
            #print(f"SWAY: \tAVERAGE: {sway_len}\tREADINGS: {sway_val}")
            #print(f"YAW:  \tAVERAGE: {yaw_len}\tREADINGS: {yaw_val}")

            print(f"SURGE: {integer_surge_valnorm}\tSWAY: {integer_sway_valnorm}\tYAW: {integer_yaw_valnorm}\tHEAVY: {integer_heavy_valnorm}\n")
            
            dataCount += 1
            packetCount += r['numPackets']
        else:
            # Got no data back from our read.
            # This only happens if your stream isn't faster than the USB read
            # timeout, ~1 sec.
            print("No data ; %s" % datetime.now())
except:
    print("".join(i for i in traceback.format_exc()))
finally:
    stop = datetime.now()
    d.streamStop()
    print("Stream stopped.\n")
    d.close()
