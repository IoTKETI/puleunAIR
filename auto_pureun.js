/**
 * Created by Wonseok Jung in KETI on 2023-02-10.
 */

const mqtt = require('mqtt');
const {nanoid} = require('nanoid');
const fs = require("fs");
const axios = require("axios");

const HOST = '121.137.228.240';

let local_mqtt_client = null;
const sub_watertemp_topic = '/puleunair/hotwater';
const sub_temphumi_topic = '/puleunair/temphumi';
const sub_auto_topic = "/puleunair/auto/set";

let hotwater = 0.0;
let humidity = 0.0;
let temperature = 0.0;

let period = {};
let heater_period = 24.0; // temperature
let spray_period = 10; // minutes
let air_period = 10; // minutes
let fan_period = 90;
let ctrl1 = 0;
let ctrl2 = 0;
let ctrl3 = 0;
let ctrl4 = 0;
let ctrl5 = 0;

let auto_mode = false;
let AUTO_val = {};
let spray_count = 0;
let air_count = 0;
let status_count = 0;
let STATUS_PERIOD = 2;

try {
    period = JSON.parse(fs.readFileSync('Profile.json', 'utf8'));

    heater_period = period.heater_period;
    spray_period = period.spray_period;
    air_period = period.air_period;
    fan_period = period.fan_period;
    ctrl1 = period.ctrl1;
    ctrl2 = period.ctrl2;
    ctrl3 = period.ctrl3;
    ctrl4 = period.ctrl4;
    ctrl5 = period.ctrl5;
} catch (e) {
    period.heater_period = heater_period;
    period.spray_period = spray_period;
    period.air_period = air_period;
    period.fan_period = fan_period;
    period.ctrl1 = 0;
    period.ctrl2 = 0;
    period.ctrl3 = 0;
    period.ctrl4 = 0;
    period.ctrl5 = 0;
    fs.writeFileSync('Profile.json', JSON.stringify(period, null, 4), 'utf8');
}

local_mqtt_connect(HOST);

function local_mqtt_connect(serverip) {
    if (local_mqtt_client === null) {
        let connectOptions = {
            host: serverip,
            port: 1883,
            protocol: "mqtt",
            keepalive: 10,
            clientId: 'local_puleunAIR_' + nanoid(15),
            protocolId: "MQTT",
            protocolVersion: 4,
            clean: true,
            reconnectPeriod: 2000,
            connectTimeout: 2000,
            rejectUnauthorized: false
        };

        local_mqtt_client = mqtt.connect(connectOptions);

        local_mqtt_client.on('connect', function () {
            console.log('local_mqtt is connected to ( ' + serverip + ' )');

            if (sub_watertemp_topic !== '') {
                local_mqtt_client.subscribe(sub_watertemp_topic);
                console.log('[local_mqtt] sub_watertemp_topic is subscribed: ' + sub_watertemp_topic);
            }
            if (sub_temphumi_topic !== '') {
                local_mqtt_client.subscribe(sub_temphumi_topic);
                console.log('[local_mqtt] sub_temphumi_topic is subscribed: ' + sub_temphumi_topic);
            }
            if (sub_auto_topic !== '') {
                local_mqtt_client.subscribe(sub_auto_topic);
                console.log('[local_mqtt] sub_auto_topic is subscribed: ' + sub_auto_topic);
            }
        });

        local_mqtt_client.on('message', function (topic, message) {
            if (topic === sub_watertemp_topic) {
                // console.log('sub_watertemp_topic - ', message.toString());
                hotwater = message.toString();
            } else if (topic === sub_temphumi_topic) {
                // console.log('sub_humidity_topic - ', message.toString());
                let temphumi_arr = message.toString().split(',');
                temperature = temphumi_arr[0];
                humidity = temphumi_arr[1];
            } else if (topic === sub_auto_topic) {
                AUTO_val = JSON.parse(message.toString());
                if (AUTO_val.hasOwnProperty('auto')) {
                    if (parseInt(AUTO_val.auto, 10) === 1) {
                        spray_count = 0;
                        air_count = 0;
                        local_mqtt_client.publish('/puleunair/Control_3/set', '1');
                        AUTO_val.ctrl3 = 1;
                        auto_mode = true;
                    }
                } else if (parseInt(AUTO_val.auto, 10) === 0) {
                    auto_mode = false;
                }
            }
        });

        local_mqtt_client.on('error', function (err) {
            console.log('[local_mqtt] (error) ' + err.message);
            local_mqtt_client = null;
            local_mqtt_connect(serverip);
        });
    }
}

setInterval(auto, 1000);

function auto() {
    if (auto_mode) {
        console.log(" AUTO MODE\n");
        // console.log("     HEATER: < %f*C\n", heater_period);
        // console.log("        AIR: %d minutes per hour\n", air_period);
        // console.log("       PUMP: always on\n");
        // console.log("        FAN: > %f%\n", fan_period);
        // console.log("      SPRAY: %d minutes per hour\n", spray_period);

        if (AUTO_val.fan_period < parseFloat(humidity)) {
            local_mqtt_client.publish('/puleunair/Control_4/set', '1');
            AUTO_val.ctrl4 = 1;
        } else if (parseFloat(humidity) < (AUTO_val.fan_period - 5)) {
            local_mqtt_client.publish('/puleunair/Control_4/set', '0');
            AUTO_val.ctrl4 = 0;
        }

        spray_count++;
        if ((0 <= spray_count) && (spray_count < (AUTO_val.spray_period * 60))) {
            local_mqtt_client.publish('/puleunair/Control_5/set', '1');
            AUTO_val.ctrl5 = 1;
        } else if (((AUTO_val.spray_period * 60) <= spray_count) && (spray_count < (60 * 60))) {
            local_mqtt_client.publish('/puleunair/Control_5/set', '0');
            AUTO_val.ctrl5 = 0;
        } else {
            spray_count = 0;
        }

        air_count++;
        if ((0 <= air_count) && (air_count < (AUTO_val.air_period * 60))) {
            local_mqtt_client.publish('/puleunair/Control_2/set', '1');
            AUTO_val.ctrl2 = 1;
        } else if (((AUTO_val.air_period * 60) <= air_count) && (air_count < (60 * 60))) {
            local_mqtt_client.publish('/puleunair/Control_2/set', '0');
            AUTO_val.ctrl2 = 0;
        } else {
            air_count = 0;
        }
    }

    if (parseFloat(hotwater) < parseFloat(AUTO_val.heater_period)) {
        local_mqtt_client.publish('/puleunair/Control_1/set', '1');
        AUTO_val.ctrl1 = 1;
    } else if ((parseFloat(AUTO_val.heater_period) + 0.4) < parseFloat(hotwater)) {
        local_mqtt_client.publish('/puleunair/Control_1/set', '0');
        AUTO_val.ctrl1 = 0;
    }

    if (local_mqtt_client !== null) {
        status_count++;
        status_count %= STATUS_PERIOD;

        if (status_count === 0) {
            local_mqtt_client.publish('/puleunair/status', JSON.stringify(AUTO_val));
            crt_cin("PureunAir/PA1/status", AUTO_val);
        }
    }
}

function crt_cin(topic, con) {
    let url = "http://" + HOST + ":7579/Mobius/" + topic;

    let data = {};
    data["m2m:cin"] = {};
    data["m2m:cin"].con = con;

    let config = {
        method: 'post',
        url: url,
        headers: {
            'Accept': 'application/json',
            'X-M2M-RI': '12345',
            'X-M2M-Origin': 'Spureunair',
            'Content-Type': 'application/json; ty=4'
        },
        data: data
    };

    axios(config)
        .then(function (response) {
            // console.log(JSON.stringify(response.data));
        })
        .catch(function (error) {
            console.log(error);
        });
}
