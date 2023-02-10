'''
import Adafruit_DHT as dht
import datetime

humi, temp = dht.read_retry(dht.DHT11, 11)

print('humi: ', humi)
print('temp:', temp)
'''

import Adafruit_DHT as dht
import time

sensor = dht.DHT11

pin = 11

try:
    while True:
        h, t = dht.read_retry(sensor, pin)

        if h is not None and t is not None:
            print("Temperature = {0:0.1f}*C Humidity = {1:0.1f}%".format(t,h))
        else:
            print("Read error")
            time.sleep(100)
except KeyboardInterrupt:
    print("Terminated by Keyboard")
finally:
    print("END")
