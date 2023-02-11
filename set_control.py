# -*- coding: utf-8 -*-
"""
 @ Created by Wonseok Jung in KETI on 2023-02-10.
"""

import paho.mqtt.client as mqtt
# import SX1509
import Control
import time

global local_mqtt_client

g_set_event = 0x00

SET_TPR = 0x01
SET_Heater = 0x02
SET_Stirrer = 0x04
SET_Lift = 0x08
SET_Lift2 = 0x10

TPR_val = 0
Heater_val = 0
Stirrer_val = 0
Lift_val = 0
Lift2_val = 0

TPR_pin = 10
Heater_pin = 11
Stirrer_pin = 12
Lift_pin = 13
Lift2_pin = 14

addr = 0x3e
# sx = SX1509.SX1509(addr)
# ctl = Control.Control(sx)


def set_TPR(val):
    # ctl.DOUT(TPR_pin, val)
    print("Control TPR - ", val)


def set_Heater(val):
    # ctl.DOUT(Heater_pin, val)
    print("Control Heater - ", val)


def set_Stirrer(val):
    # ctl.DOUT(Stirrer_pin, val)
    print("Control Stirrer - ", val)


def set_Lift(val):
    # ctl.DOUT(Lift_pin, val)
    print("Control Lift - ", val)


def set_Lift2(val):
    # ctl.DOUT(Lift2_pin, val)
    print("Control Lift2 - ", val)


def on_connect(client, userdata, flags, rc):
    # 0: Connection successful
    # 1: Connection refused - incorrect protocol version
    # 2: Connection refused - invalid client identifier
    # 3: Connection refused - server unavailable
    # 4: Connection refused - bad username or password
    # 5: Connection refused - not authorised
    # 6-255: Currently unused.
    if rc is 0:
        print('[local_mqtt_client_connect] connect to 127.0.0.1')
        local_mqtt_client.subscribe("/puleunair/TPR/set")
        local_mqtt_client.subscribe("/puleunair/Heater/set")
        local_mqtt_client.subscribe("/puleunair/Stirrer/set")
        local_mqtt_client.subscribe("/puleunair/Lift/set")
        local_mqtt_client.subscribe("/puleunair/Lift2/set")
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
    global SET_TPR
    global SET_Heater
    global SET_Stirrer
    global SET_Lift
    global SET_Lift2
    global TPR_val
    global Heater_val
    global Stirrer_val
    global Lift_val
    global Lift2_val

    if _msg.topic == '/puleunair/TPR/set':
        TPR_val = _msg.payload.decode('utf-8')
        g_set_event |= SET_TPR
    elif _msg.topic == '/puleunair/Heater/set':
        Heater_val = _msg.payload.decode('utf-8')
        g_set_event |= SET_Heater
    elif _msg.topic == '/puleunair/Stirrer/set':
        Stirrer_val = _msg.payload.decode('utf-8')
        g_set_event |= SET_Stirrer
    elif _msg.topic == '/puleunair/Lift/set':
        Lift_val = _msg.payload.decode('utf-8')
        g_set_event |= SET_Lift
    elif _msg.topic == '/puleunair/Lift2/set':
        Lift2_val = _msg.payload.decode('utf-8')
        g_set_event |= SET_Lift2
    else:
        print("Received " + _msg.payload.decode('utf-8') + " From " + _msg.topic)


if __name__ == "__main__":
    local_mqtt_client = mqtt.Client()
    local_mqtt_client.on_connect = on_connect
    local_mqtt_client.on_disconnect = on_disconnect
    local_mqtt_client.on_subscribe = on_subscribe
    local_mqtt_client.on_message = on_message
    local_mqtt_client.connect("127.0.0.1", 1883)

    local_mqtt_client.loop_start()

    while True:
        if g_set_event & SET_TPR:
            g_set_event &= (~SET_TPR)
            set_TPR(TPR_val)
        elif g_set_event & SET_Heater:
            g_set_event &= (~SET_Heater)
            set_Heater(Heater_val)
        elif g_set_event & SET_Stirrer:
            g_set_event &= (~SET_Stirrer)
            set_Stirrer(Stirrer_val)
        elif g_set_event & SET_Lift:
            g_set_event &= (~SET_Lift)
            set_Lift(Lift_val)
        elif g_set_event & SET_Lift2:
            g_set_event &= (~SET_Lift2)
            set_Lift2(Lift2_val)
#
# count = 0
#
# while True:
#     count += 1
#     count %= 2
#     ctl.DOUT(TPR_pin, count)
#     ctl.DOUT(Heater_pin, count)
#     ctl.DOUT(Stirrer_pin, count)
#     ctl.DOUT(Lift_pin, count)
#     ctl.DOUT(Lift2_pin, count)
#     print(count)
#     time.sleep(1)
