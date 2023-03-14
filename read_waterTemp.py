import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
from DFRobot_MAX31855 import *
import paho.mqtt.client as mqtt
import threading
from datetime import datetime

pureunHost = '121.137.228.240'

mqtt_client = None
pub_hotwater_topic = "/puleunair/hotwater"

I2C_BUS = 6
I2C_ADDRESS = 0x10

max31855 = DFRobot_MAX31855(I2C_BUS, I2C_ADDRESS)


def read_hotwater():
    global max31855
    global mqtt_client
    global pub_hotwater_topic

    temp = max31855.read_celsius()
    if mqtt_client is not None:
        mqtt_client.publish(pub_hotwater_topic, temp)
    else:
        mqtt_client.reconnect()

    print('\n', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f') + " Water Temperature:%s C" % temp)

    threading.Timer(2, read_hotwater).start()


def on_connect(client, userdata, flags, rc):
    # 0: Connection successful
    # 1: Connection refused - incorrect protocol version
    # 2: Connection refused - invalid client identifier
    # 3: Connection refused - server unavailable
    # 4: Connection refused - bad username or password
    # 5: Connection refused - not authorised
    # 6-255: Currently unused.
    global mqtt_client
    global pureunHost

    if rc is 0:
        print('[mqtt_client_connect] connect to ' + pureunHost)
    elif rc is 1:
        print("incorrect protocol version")
        mqtt_client.reconnect()
    elif rc is 2:
        print("invalid client identifier")
        mqtt_client.reconnect()
    elif rc is 3:
        print("server unavailable")
        mqtt_client.reconnect()
    elif rc is 4:
        print("bad username or password")
        mqtt_client.reconnect()
    elif rc is 5:
        print("not authorised")
        mqtt_client.reconnect()
    else:
        print("Currently unused.")
        mqtt_client.reconnect()


def on_disconnect(client, userdata, flags, rc=0):
    print(str(rc))


def on_subscribe(client, userdata, mid, granted_qos):
    print("subscribed: " + str(mid) + " " + str(granted_qos))


def on_message(client, userdata, _msg):
    print("Received " + _msg.payload.decode('utf-8') + " From " + _msg.topic)


if __name__ == "__main__":
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_subscribe = on_subscribe
    mqtt_client.on_message = on_message
    mqtt_client.connect("121.137.228.240", 1883)

    mqtt_client.loop_start()

    read_hotwater()
