# -*- coding: utf-8 -*-
"""
 @ Created by Wonseok Jung in KETI on 2023-02-10.
"""
import time

import paho.mqtt.client as mqtt
import SX1509
import Control
import json
import threading

local_mqtt_client = None

g_set_event = 0x00

SET_Control1 = 0x01
SET_Control2 = 0x02
SET_Control3 = 0x04
SET_Control4 = 0x08
SET_Control5 = 0x10
SET_AUTO = 0x20

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

hotwater = 0.0
temperature = 0.0
humidity = 0.0

auto_mode = False
spray_count = 0
air_count = 0


def set_Control1(val):
    ctl.DOUT(Control1_pin, val)
    print("Control Control1 - ", val)


def set_Control2(val):
    ctl.DOUT(Control2_pin, val)
    print("Control Control2 - ", val)


def set_Control3(val):
    ctl.DOUT(Control3_pin, val)
    print("Control Control3 - ", val)


def set_Control4(val):
    ctl.DOUT(Control4_pin, val)
    print("Control Control4 - ", val)


def set_Control5(val):
    ctl.DOUT(Control5_pin, val)
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

    if rc is 0:
        print('[local_mqtt_client_connect] connect to 127.0.0.1')
        local_mqtt_client.subscribe("/puleunair/Control_1/set")
        local_mqtt_client.subscribe("/puleunair/Control_2/set")
        local_mqtt_client.subscribe("/puleunair/Control_3/set")
        local_mqtt_client.subscribe("/puleunair/Control_4/set")
        local_mqtt_client.subscribe("/puleunair/Control_5/set")
        local_mqtt_client.subscribe("/puleunair/auto/set")
        local_mqtt_client.subscribe("/puleunair/temperature")
        local_mqtt_client.subscribe("/puleunair/humidity")
        local_mqtt_client.subscribe("/puleunair/hotwater")
    elif rc is 1:
        print("incorrect protocol version")
        local_mqtt_client.reconnect()
    elif rc is 2:
        print("invalid client identifier")
        local_mqtt_client.reconnect()
    elif rc is 3:
        print("server unavailable")
        local_mqtt_client.reconnect()
    elif rc is 4:
        print("bad username or password")
        local_mqtt_client.reconnect()
    elif rc is 5:
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
    global SET_AUTO
    global Control1_val
    global Control2_val
    global Control3_val
    global Control4_val
    global Control5_val
    global AUTO_val
    global hotwater
    global temperature
    global humidity
    global auto_mode

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
    elif _msg.topic == '/puleunair/auto/set':
        AUTO_val = json.loads(_msg.payload.decode('utf-8'))
        g_set_event |= SET_AUTO
    elif _msg.topic == '/puleunair/hotwater':
        hotwater = float(_msg.payload.decode('utf-8'))
    elif _msg.topic == '/puleunair/temperature':
        temperature = float(_msg.payload.decode('utf-8'))
    elif _msg.topic == '/puleunair/humidity':
        humidity = float(_msg.payload.decode('utf-8'))
    else:
        print("Received " + _msg.payload.decode('utf-8') + " From " + _msg.topic)


def auto():
    global AUTO_val
    global hotwater
    global temperature
    global humidity
    global auto_mode
    global spray_count
    global air_count

    if auto_mode:
        print(" AUTO MODE\n")
        print("     HEATER: < %f*C\n", AUTO_val["heater_period"])
        print("        AIR: %d minutes per hour\n", AUTO_val["air_period"])
        print("       PUMP: always on\n")
        print("        FAN: > %f%\n", AUTO_val["fan_period"])
        print("      SPRAY: %d minutes per hour\n", AUTO_val["spray_period"])

        if float(humidity) > AUTO_val["fan_period"]:
            set_Control4(1)
        elif float(humidity) < (AUTO_val["fan_period"] - 5):
            set_Control4(0)

        spray_count += 1
        if (0 <= spray_count) and (spray_count < (AUTO_val["spray_period"] * 60)):
            set_Control5(1)
        elif ((AUTO_val["spray_period"] * 60) <= spray_count) and (spray_count < (60 * 60)):
            set_Control5(0)
        else:
            spray_count = 0

        air_count += 1
        if (0 <= air_count) and (air_count < (AUTO_val["air_period"] * 60)):
            set_Control2(1)
        elif ((AUTO_val["air_period"] * 60) <= air_count) and (air_count < (60 * 60)):
            set_Control2(0)
        else:
            air_count = 0

    if float(hotwater) < AUTO_val["heater_period"]:
        set_Control1(1)
    elif float(hotwater) > AUTO_val["heater_period"] + 0.4:
        set_Control1(0)

    threading.Timer(1, auto).start()


if __name__ == "__main__":
    local_mqtt_client = mqtt.Client()
    local_mqtt_client.on_connect = on_connect
    local_mqtt_client.on_disconnect = on_disconnect
    local_mqtt_client.on_subscribe = on_subscribe
    local_mqtt_client.on_message = on_message
    local_mqtt_client.connect("127.0.0.1", 1883)

    local_mqtt_client.loop_start()

    auto()

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
        elif g_set_event & SET_AUTO:
            g_set_event &= (~SET_AUTO)
            if AUTO_val.get('auto'):
                if int(AUTO_val["auto"]) == 1:
                    spray_count = 0
                    air_count = 0
                    auto_mode = True
                else:
                    auto_mode = False
