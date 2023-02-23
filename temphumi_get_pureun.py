# -*- coding: utf-8 -*-
"""
 @ Created by Wonseok Jung in KETI on 2023-02-10.
"""
import paho.mqtt.client as mqtt
import json
import threading
import requests
from datetime import datetime

import Adafruit_DHT as dht

HOST = '121.137.228.240'

local_mqtt_client = None

# Temperature & Humidity Pin
pin = 11
sensor = dht.DHT22

get_temphumi_interval = 2.0

temperature = 0.0
humidity = 0.0


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


def get_temphumi():
    global get_temphumi_interval
    global temperature
    global humidity
    global pin
    global sensor

    try:
        humi, temp = dht.read_retry(sensor, pin)

        if humi is not None and temp is not None:
            print(datetime.now().strftime('%Y.%m.%d - %H:%M:%S'))
            print("Temperature = {0:0.1f}*C Humidity = {1:0.1f}%".format(temp, humi))
            if (0.0 <= humi and humi <= 100.0):
                humidity = humi
            else:
                print('Humidity error')

            if (-18.0 < temp and temp < 100.0):
                temperature = temp
            else:
                print('Temperature error')
        else:
            print("Read error")
            threading.Timer(1.0, get_temphumi).start()
    except KeyboardInterrupt:
        print("Terminated by Keyboard")

    threading.Timer(get_temphumi_interval, get_temphumi).start()


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


temphumi_count = 0
TEMPHUMI_PERIOD = get_temphumi_interval


def auto():
    global temperature
    global humidity
    global local_mqtt_client
    global temphumi_count
    global TEMPHUMI_PERIOD

    if local_mqtt_client is not None:
        temphumi_count += 1
        temphumi_count %= TEMPHUMI_PERIOD

        if temphumi_count == 0:
            temphumi = str(temperature) + ',' + str(humidity)
            local_mqtt_client.publish('/puleunair/temphumi', temphumi)
            crt_cin("PureunAir/PA1/temp", temphumi)

    threading.Timer(1.0, auto).start()


if __name__ == "__main__":
    local_mqtt_client = mqtt.Client()
    local_mqtt_client.on_connect = on_connect
    local_mqtt_client.on_disconnect = on_disconnect
    local_mqtt_client.on_subscribe = on_subscribe
    local_mqtt_client.on_message = on_message
    local_mqtt_client.connect(HOST, 1883)

    auto()

    get_temphumi()

    local_mqtt_client.loop_forever()
