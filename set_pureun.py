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

import SX1509
import Control

HOST = '121.137.228.240'

local_mqtt_client = None
pub_status_topic = '/puleunair/status'

g_set_event = 0x00

SET_Control1 = 0x01
SET_Control2 = 0x02
SET_Control3 = 0x04
SET_Control4 = 0x08
SET_Control5 = 0x10

Control1_val = 0
Control2_val = 0
Control3_val = 0
Control4_val = 0
Control5_val = 0
AUTO_val = dict()

Control1_pin = 10
Control2_pin = 11
Control3_pin = 12
Control4_pin = 13
Control5_pin = 14

i2c_addr = 0x3e
i2c_bus = 2
sx = SX1509.SX1509(i2c_addr, i2c_bus)
ctl = Control.Control(sx)

temperature = 0.0
humidity = 0.0
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


def set_Control1(val):
    global AUTO_val

    ctl.DOUT(Control1_pin, val)
    AUTO_val["ctrl1"] = val
    print("Control Control1 - ", val)


def set_Control2(val):
    global AUTO_val

    ctl.DOUT(Control2_pin, val)
    AUTO_val["ctrl2"] = val
    print("Control Control2 - ", val)


def set_Control3(val):
    global AUTO_val

    ctl.DOUT(Control3_pin, val)
    AUTO_val["ctrl3"] = val
    print("Control Control3 - ", val)


def set_Control4(val):
    global AUTO_val

    ctl.DOUT(Control4_pin, val)
    AUTO_val["ctrl4"] = val
    print("Control Control4 - ", val)


def set_Control5(val):
    global AUTO_val

    ctl.DOUT(Control5_pin, val)
    AUTO_val["ctrl5"] = val
    print("Control Control5 - ", val)


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
        local_mqtt_client.subscribe("/puleunair/Control_1/set")
        local_mqtt_client.subscribe("/puleunair/Control_2/set")
        local_mqtt_client.subscribe("/puleunair/Control_3/set")
        local_mqtt_client.subscribe("/puleunair/Control_4/set")
        local_mqtt_client.subscribe("/puleunair/Control_5/set")
        local_mqtt_client.subscribe("/puleunair/auto/set")
        local_mqtt_client.subscribe("/puleunair/hotwater")
        local_mqtt_client.subscribe("/puleunair/temphumi")
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
    global g_set_event
    global SET_Control1
    global SET_Control2
    global SET_Control3
    global SET_Control4
    global SET_Control5
    global Control1_val
    global Control2_val
    global Control3_val
    global Control4_val
    global Control5_val
    global AUTO_val
    global auto_mode
    global temperature
    global humidity
    global hotwater

    if _msg.topic == '/puleunair/Control_1/set':
        Control1_val = int(_msg.payload.decode('utf-8'))
        g_set_event |= SET_Control1
    elif _msg.topic == '/puleunair/Control_2/set':
        Control2_val = int(_msg.payload.decode('utf-8'))
        g_set_event |= SET_Control2
    elif _msg.topic == '/puleunair/Control_3/set':
        Control3_val = int(_msg.payload.decode('utf-8'))
        g_set_event |= SET_Control3
    elif _msg.topic == '/puleunair/Control_4/set':
        Control4_val = int(_msg.payload.decode('utf-8'))
        g_set_event |= SET_Control4
    elif _msg.topic == '/puleunair/Control_5/set':
        Control5_val = int(_msg.payload.decode('utf-8'))
        g_set_event |= SET_Control5
    elif _msg.topic == '/puleunair/hotwater':
        hotwater = float(_msg.payload.decode('utf-8'))
    elif _msg.topic == '/puleunair/temphumi':
        temphumi = _msg.payload.decode('utf-8')
        temphumi_arr = temphumi.split(',')
        temperature = temphumi_arr[0]
        humidity = temphumi_arr[1]
    else:
        print("Received " + _msg.payload.decode('utf-8') + " From " + _msg.topic)


if __name__ == "__main__":
    local_mqtt_client = mqtt.Client()
    local_mqtt_client.on_connect = on_connect
    local_mqtt_client.on_disconnect = on_disconnect
    local_mqtt_client.on_subscribe = on_subscribe
    local_mqtt_client.on_message = on_message
    local_mqtt_client.connect(HOST, 1883)

    local_mqtt_client.loop_start()

    try:
        with open('Profile.json', 'r') as user_file:
            AUTO_val = json.loads(user_file.read())
    except Exception as e:
        AUTO_val["heater_period"] = 24.0
        AUTO_val["spray_period"] = 10
        AUTO_val["air_period"] = 10
        AUTO_val["fan_period"] = 90
        AUTO_val["ctrl1"] = 0
        AUTO_val["ctrl2"] = 0
        AUTO_val["ctrl3"] = 0
        AUTO_val["ctrl4"] = 0
        AUTO_val["ctrl5"] = 0

        with open('Profile.json', 'w') as outfile:
            json.dump(AUTO_val, outfile, indent=4)

    while True:
        if g_set_event & SET_Control1:
            g_set_event &= (~SET_Control1)
            set_Control1(Control1_val)
        elif g_set_event & SET_Control2:
            g_set_event &= (~SET_Control2)
            set_Control2(Control2_val)
        elif g_set_event & SET_Control3:
            g_set_event &= (~SET_Control3)
            set_Control3(Control3_val)
        elif g_set_event & SET_Control4:
            g_set_event &= (~SET_Control4)
            set_Control4(Control4_val)
        elif g_set_event & SET_Control5:
            g_set_event &= (~SET_Control5)
            set_Control5(Control5_val)
