# -*- coding: utf-8 -*-
"""
 @ Created by Wonseok Jung in KETI on 2023-02-10.
"""

import paho.mqtt.client as mqtt
import max6675
import Adafruit_DHT as dht
import time

global local_mqtt_client
pub_hotwater_topic = "/puleunair/hotwater/res"
pub_humi_topic = "/puleunair/humi/res"

g_res_event = 0x00

RES_HOTWATER = 0x01
RES_TEMPHUMI = 0x02

# MAX6675
cs = 18
sck = 20
so = 16
# Humidity
pin = 11


def get_hotwater(cs, sck, so):
    max6675.set_pin(cs, sck, so, 1)

    try:
        while True:
            temp = max6675.read_temp(cs)
            temp = round(temp, 1)
            print("Hot Water Temperature = {0:0.1f}*C".format(temp))

            max6675.time.sleep(2)

    except KeyboardInterrupt:
        pass

    return temp


def get_temphumi(out_pin):
    sensor = dht.DHT11
    try:
        while True:
            h, t = dht.read_retry(sensor, out_pin)

            if h is not None and t is not None:
                print("Temperature = {0:0.1f}*C Humidity = {1:0.1f}%".format(t, h))
            else:
                print("Read error")
                time.sleep(100)
    except KeyboardInterrupt:
        print("Terminated by Keyboard")
    finally:
        print("END")

    return h


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
        local_mqtt_client.subscribe("/puleunair/hotwater/req")
        local_mqtt_client.subscribe("/puleunair/humi/req")
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
    global g_res_event
    global RES_HOTWATER
    global RES_TEMPHUMI

    if _msg.topic == '/puleunair/hotwater/req':
        g_res_event |= RES_HOTWATER
    elif _msg.topic == '/puleunair/humi/req':
        g_res_event |= RES_TEMPHUMI
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
        if g_res_event & RES_HOTWATER:
            g_res_event &= (~RES_HOTWATER)
            g_res_hotwater = get_hotwater(cs, sck, so)
            local_mqtt_client.publish(pub_hotwater_topic, g_res_hotwater)

        elif g_res_event & RES_TEMPHUMI:
            g_res_event &= (~RES_TEMPHUMI)
            g_res_humi = get_temphumi(pin)
            local_mqtt_client.publish(pub_humi_topic, g_res_humi)
