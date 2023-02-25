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

# import max6675
import os
import glob
import Adafruit_DHT as dht
import SX1509
import Control

HOST = '121.137.228.240'

local_mqtt_client = None
pub_status_topic = '/puleunair/status'
pub_hotwater_topic = "/puleunair/hotwater/res"
pub_humi_topic = "/puleunair/humi/res"

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

# Temperature & Humidity Pin
pin = 11

get_hotwater_interval = 2.0
get_temphumi_interval = 2.0

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

t_auto = None

arrAutoHumidity = [0 for i in range(1800)]
arrAutoHotwater = [0 for i in range(1800)]


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

    response = requests.request("POST", url, headers=headers, data=json.dumps(payload))

    # print(response.headers['X-M2M-RSC'], '-', response.text)


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


# try:
#     temp = max6675.read_temp(cs)
#     hotwater = round(temp, 1)
#     print("Hot Water Temperature = {0:0.1f}*C".format(hotwater))
#     if local_mqtt_client is not None:
#         if hotwater < 0.0 or hotwater > 50.0:
#             temp = max6675.read_temp(cs)
#             hotwater = round(temp, 1)
#             print("Hot Water Temperature = {0:0.1f}*C".format(hotwater))
#         else:
#             local_mqtt_client.publish('/puleunair/hotwater', hotwater)
#             crt_cin("PureunAir/PA1/hotwater", hotwater)
#     else:
#         local_mqtt_client.reconnect()
#
# except KeyboardInterrupt:
#     pass
#
# threading.Timer(get_hotwater_interval, get_hotwater, args=[cs]).start()


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
        local_mqtt_client.subscribe("/puleunair/req/arrAutoHumidity")
        local_mqtt_client.subscribe("/puleunair/req/arrAutoHotwater")

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
    global SET_AUTO
    global Control1_val
    global Control2_val
    global Control3_val
    global Control4_val
    global Control5_val
    global AUTO_val
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
        recv_auto_val = json.loads(_msg.payload.decode('utf-8'))
        for key in recv_auto_val.keys():
            AUTO_val[key] = recv_auto_val[key]
        g_set_event |= SET_AUTO
    elif _msg.topic == '/puleunair/req/arrAutoHumidity':
        local_mqtt_client.publish('/puleunair/res/arrAutoHumidity', str(arrAutoHumidity))
    elif _msg.topic == '/puleunair/req/arrAutoHotwater':
        local_mqtt_client.publish('/puleunair/res/arrAutoHotwater', str(arrAutoHotwater))
    else:
        print("Received " + _msg.payload.decode('utf-8') + " From " + _msg.topic)


status_count = 0
STATUS_PERIOD = 2

temphumi_count = 0
TEMPHUMI_PERIOD = get_temphumi_interval

hotwater_count = 0
HOTWATER_PERIOD = get_hotwater_interval


def auto():
    global AUTO_val
    global hotwater
    global temperature
    global humidity
    global auto_mode
    global spray_count
    global air_count
    global local_mqtt_client
    global pub_status_topic
    global status_count
    global STATUS_PERIOD
    global temphumi_count
    global TEMPHUMI_PERIOD
    global hotwater_count
    global HOTWATER_PERIOD

    if auto_mode:
        print(" AUTO MODE\n")
        # print("     HEATER: < %f*C\n", AUTO_val["heater_period"])
        # print("        AIR: %d minutes per hour\n", AUTO_val["air_period"])
        # print("       PUMP: always on\n")
        # print("        FAN: > %f%\n", AUTO_val["fan_period"])
        # print("      SPRAY: %d minutes per hour\n", AUTO_val["spray_period"])

        if AUTO_val["fan_period"] < float(humidity):
            set_Control4(1)
        # elif (AUTO_val["fan_period"]-5) <= float(humidity) and float(humidity) <= AUTO_val["fan_period"]:
        #     set_Control4(1)
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

    if float(hotwater) < float(AUTO_val["heater_period"]):
        set_Control1(1)
    # elif float(AUTO_val["heater_period"]) <= float(hotwater) and float(hotwater) <= float(AUTO_val["heater_period"])+0.4:
    #         set_Control1(1)
    elif float(AUTO_val["heater_period"]) + 0.4 < float(hotwater):
        set_Control1(0)

    if local_mqtt_client is not None:
        status_count += 1
        status_count %= STATUS_PERIOD

        if status_count == 0:
            local_mqtt_client.publish(pub_status_topic, json.dumps(AUTO_val))
            crt_cin("PureunAir/PA1/status", AUTO_val)

        temphumi_count += 1
        temphumi_count %= TEMPHUMI_PERIOD

        if temphumi_count == 0:
            temphumi = str(temperature) + ',' + str(humidity)
            local_mqtt_client.publish('/puleunair/temphumi', temphumi)
            crt_cin("PureunAir/PA1/temp", temphumi)

            if auto_mode:
                arrAutoHumidity.pop(0)
                arrAutoHumidity.append(humidity)
            else:
                arrAutoHumidity = [0 for i in range(1800)]

        hotwater_count += 1
        hotwater_count %= HOTWATER_PERIOD

        if hotwater_count == 0:
            local_mqtt_client.publish('/puleunair/hotwater', hotwater)
            crt_cin("PureunAir/PA1/hotwater", hotwater)

            if auto_mode:
                arrAutoHotwater.pop(0)
                arrAutoHotwater.append(hotwater)
            else:
                arrAutoHotwater = [0 for i in range(1800)]

    threading.Timer(1.0, auto).start()


#
# def sendStatus():
#     global local_mqtt_client
#     global pub_status_topic
#
#     if local_mqtt_client is not None:
#         local_mqtt_client.publish(pub_status_topic, json.dumps(AUTO_val))
#         crt_cin("PureunAir/PA1/status", AUTO_val)
#
#     threading.Timer(2.0, sendStatus).start()

sensor = dht.DHT22

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
        AUTO_val["auto"] = 0
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

    auto()
    #     sendStatus()

    # max6675.set_pin(cs, sck, so, 1)

    get_hotwater()

    get_temphumi()
    # get_temphumi(ctl.DIN(th_pin))

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
            if int(AUTO_val["auto"]) == 1:
                spray_count = 0
                air_count = 0
                set_Control3(1)
                auto_mode = True
            elif int(AUTO_val["auto"]) == 0:
                auto_mode = False
