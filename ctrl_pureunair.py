# -*- coding: utf-8 -*-
"""
 @ Created by Wonseok Jung in KETI on 2023-02-10.
"""
import paho.mqtt.client as mqtt
import time
import json
import threading

import SX1509
import Control

HOST = 'localhost'

local_mqtt_client = None
pub_status_topic = '/puleunair/status'

g_set_event = 0x00

SET_Control1 = 0x01
SET_Control2 = 0x02
SET_Control3 = 0x04
SET_Control4 = 0x08
SET_Control5 = 0x10
SET_STATUS_PERIOD = 0x40

Control1_val = 0
Control2_val = 0
Control3_val = 0
Control4_val = 0
Control5_val = 0
STATUS_val = dict()

Control1_pin = 10
Control2_pin = 11
Control3_pin = 12
Control4_pin = 13
Control5_pin = 14

i2c_addr = 0x3e
i2c_bus = 2
sx = SX1509.SX1509(i2c_addr, i2c_bus)
ctl = Control.Control(sx)

def set_Control1(val):
    global STATUS_val

    ctl.DOUT(Control1_pin, val)
    STATUS_val["ctrl1"] = val
    print("Control Control1 - ", val)


def set_Control2(val):
    global STATUS_val

    ctl.DOUT(Control2_pin, val)
    STATUS_val["ctrl2"] = val
    print("Control Control2 - ", val)


def set_Control3(val):
    global STATUS_val

    ctl.DOUT(Control3_pin, val)
    STATUS_val["ctrl3"] = val
    print("Control Control3 - ", val)


def set_Control4(val):
    global STATUS_val

    ctl.DOUT(Control4_pin, val)
    STATUS_val["ctrl4"] = val
    print("Control Control4 - ", val)


def set_Control5(val):
    global STATUS_val

    ctl.DOUT(Control5_pin, val)
    STATUS_val["ctrl5"] = val
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
        local_mqtt_client.subscribe("/pureunair/status/param/set/interval")

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
    global STATUS_PERIOD

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
    elif _msg.topic == '/pureunair/status/param/set/interval':
        STATUS_PERIOD = int(_msg.payload.decode('utf-8'))
    else:
        print("Received " + _msg.payload.decode('utf-8') + " From " + _msg.topic)


STATUS_PERIOD = 2
def sensingStatus():
    global STATUS_PERIOD
    global g_set_event

    g_set_event |= SET_STATUS_PERIOD

    threading.Timer(STATUS_PERIOD, sensingStatus).start()

if __name__ == "__main__":
    local_mqtt_client = mqtt.Client()
    local_mqtt_client.on_connect = on_connect
    local_mqtt_client.on_disconnect = on_disconnect
    local_mqtt_client.on_subscribe = on_subscribe
    local_mqtt_client.on_message = on_message
    local_mqtt_client.connect(HOST, 1883)

    local_mqtt_client.loop_start()

    Control1_val = 0
    Control2_val = 0
    Control3_val = 0
    Control4_val = 0
    Control5_val = 0

    STATUS_val["ctrl1"] = Control1_val
    STATUS_val["ctrl2"] = Control1_val
    STATUS_val["ctrl3"] = Control1_val
    STATUS_val["ctrl4"] = Control1_val
    STATUS_val["ctrl5"] = Control1_val

    set_Control1(0)
    set_Control2(0)
    set_Control3(0)
    set_Control4(0)
    set_Control5(0)

    sensingStatus()

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
        elif g_set_event & SET_STATUS_PERIOD:
            g_set_event &= (~SET_STATUS_PERIOD)
            if local_mqtt_client is not None:
                local_mqtt_client.publish(pub_status_topic, json.dumps(STATUS_val))

