const sensor = require("node-dht-sensor");
const sensor_ds18b20 = require('ds18b20-raspi');
const {nanoid} = require("nanoid");
const mqtt = require("mqtt");

let local_mqtt_client = null;

local_mqtt_connect('localhost');

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

        local_mqtt_client.on('connect', () => {
            console.log('local_mqtt is connected to ( ' + serverip + ' )');

            local_mqtt_client.subscribe('/pureunair/temphumi/param/set/interval');
        });

        local_mqtt_client.on('message', (topic, message) => {
            if (topic === '/pureunair/temphumi/param/set/interval') {
                console.log(topic, message.tostring());

                let interval = parseInt(message.toString());
                sensingTempHumi(interval);
            }
        });

        local_mqtt_client.on('error', (err) => {
            console.log('[local_mqtt] (error) ' + err.message);
            local_mqtt_client = null;
            local_mqtt_connect(serverip);
        });
    }
}

let sendHotwater = (err, tempC, callback) => {
    if (!err) {
        console.log('Water Temperature: ' + `${tempC}°C`);
        if (local_mqtt_client) {
            preCount = 0;
            local_mqtt_client.publish('/puleunair/hotwater', tempC.toString() + ',' + preCount.toString());
            preTempC = tempC;
        }
        callback();
    }
    else {
        if (local_mqtt_client) {
            preCount++;
            local_mqtt_client.publish('/puleunair/hotwater', preTempC.toString() + ',' + preCount.toString());
        }
        callback();
    }
}


let sendTemphumi = (err, temperature, humidity, callback) => {
    if (!err) {
        console.log(`temp: ${temperature}°C, humidity: ${humidity}%`);
        if (local_mqtt_client) {
            preCount = 0;
            local_mqtt_client.publish('/puleunair/temphumi', (temperature.toString() + ',' + humidity.toString() + ',' + preCount.toString()));
            preTemperature = temperature;
            preHumidity = humidity;
        }
        callback();
    }
    else {
        if (local_mqtt_client) {
            preCount++;
            local_mqtt_client.publish('/puleunair/temphumi', (preTemperature.toString() + ',' + preHumidity.toString() + ',' + preCount.toString()));
        }
        callback();
    }
}

let preTemperature = 0;
let preHumidity = 0;
let preCount = 0;
let preTempC = 0;
let sensingTempHumi = (interval) => {
    if(sensingTid) {
        clearInterval(sensingTid);
    }

    sensingTid = setInterval(() => {
        sensor.read(22, 11, (err, temperature, humidity) => {
            sendTemphumi(err, temperature, humidity, () => {
                sensor_ds18b20.readSimpleC(1, (err, tempC) => {
                    sendHotwater(err, tempC);
                });
            });
        });
    }, interval);
}

let sensingTid = null;
sensingTempHumi(3000);
