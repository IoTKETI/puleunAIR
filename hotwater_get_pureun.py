# -*- coding: utf-8 -*-
"""
 @ Created by Wonseok Jung in KETI on 2023-02-10.
"""
import paho.mqtt.client as mqtt
import time
import json
import threading
import requests
from datetime import datetime

import os
import glob

HOST = '121.137.228.240'

local_mqtt_client = None

'''
# MAX6675
cs = 18
sck = 20
so = 16
'''
# DS18B20
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28-3ca*')[0]
device_file = device_folder + '/w1_slave'

get_hotwater_interval = 2.0

hotwater = 0.0


def crt_cin(url, con):
    global HOST

    url = "http://" + HOST + ":7579/Mobius/" + url

    payload = dict()
    payload["m2m:cin"] = dict()
    payload["m2m:cin"]["con"] = con

    headers = {
        'Accept': 'application/json',
        'X-M2M-RI': '12345',
        'X-M2M-Origin': 'Spureunair',
        'Content-Type': 'application/json; ty=4'
    }

    requests.request("POST", url, headers=headers, data=json.dumps(payload))


def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines


def get_hotwater():
    global get_hotwater_interval
    global hotwater

    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos + 2:]
        hotwater = float(temp_string) / 1000.0
        print(datetime.now().strftime('%Y.%m.%d - %H:%M:%S'))
        print("Hotwater = {0:0.1f}*C".format(hotwater))

    threading.Timer(get_hotwater_interval, get_hotwater).start()


def on_connect(client, userdata, flags, rc):
    # 0: Connection successful
    # 1: Connection refused - incorrect protocol version
    # 2: Connection refused - invalid client identifier
    # 3: Connection refused - server unavailable
    # 4: Connection refused - bad username or password
    # 5: Connection refused - not authorised
    # 6-255: Currently unused.

    global local_mqtt_client
    global HOST

    if rc == 0:
        print('[local_mqtt_client_connect] connect to ' + HOST)
    elif rc == 1:
        print("incorrect protocol version")
        local_mqtt_client.reconnect()
    elif rc == 2:
        print("invalid client identifier")
        local_mqtt_client.reconnect()
    elif rc == 3:
        print("server unavailable")
        local_mqtt_client.reconnect()
    elif rc == 4:
        print("bad username or password")
        local_mqtt_client.reconnect()
    elif rc == 5:
        print("not authorised")
        local_mqtt_client.reconnect()
    else:
        print("Currently unused.")
        local_mqtt_client.reconnect()


def on_disconnect(client, userdata, flags, rc=0):
    print(str(rc))


def on_subscribe(client, userdata, mid, granted_qos):
    print("subscribed: " + str(mid) + " " + str(granted_qos))


def on_message(client, userdata, _msg):
    print("Received " + _msg.payload.decode('utf-8') + " From " + _msg.topic)


status_count = 0
STATUS_PERIOD = 2

hotwater_count = 0
HOTWATER_PERIOD = get_hotwater_interval


def auto():
    global hotwater
    global local_mqtt_client
    global pub_status_topic
    global status_count
    global STATUS_PERIOD
    global hotwater_count
    global HOTWATER_PERIOD

    if local_mqtt_client is not None:
        hotwater_count += 1
        hotwater_count %= HOTWATER_PERIOD

        if hotwater_count == 0:
            local_mqtt_client.publish('/puleunair/hotwater', hotwater)
            crt_cin("PureunAir/PA1/hotwater", hotwater)

    threading.Timer(1.0, auto).start()


if __name__ == "__main__":
    local_mqtt_client = mqtt.Client()
    local_mqtt_client.on_connect = on_connect
    local_mqtt_client.on_disconnect = on_disconnect
    local_mqtt_client.on_subscribe = on_subscribe
    local_mqtt_client.on_message = on_message
    local_mqtt_client.connect(HOST, 1883)

    auto()

    get_hotwater()

    local_mqtt_client.loop_forever()
