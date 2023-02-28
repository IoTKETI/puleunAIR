const sensor = require("node-dht-sensor");
const {nanoid} = require("nanoid");
const mqtt = require("mqtt");
const axios = require('axios');

let local_mqtt_client = null;

local_mqtt_connect('gcs.iotocean.org');

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

            local_mqtt_client.subscribe('/puleunair/req/arrAutoTemperature');
            local_mqtt_client.subscribe('/puleunair/req/arrAutoHumidity');
        });

        local_mqtt_client.on('message', (topic, message) => {
            if (topic === '/puleunair/req/arrAutoTemperature') {
                local_mqtt_client.publish('/puleunair/res/arrAutoTemperature', JSON.stringify(arrTemperature));
            } else if (topic === '/puleunair/req/arrAutoHumidity') {
                local_mqtt_client.publish('/puleunair/res/arrAutoHumidity', JSON.stringify(arrHumidity));
            }
        });

        local_mqtt_client.on('error', (err) => {
            console.log('[local_mqtt] (error) ' + err.message);
            local_mqtt_client = null;
            local_mqtt_connect(serverip);
        });
    }
}

const SAMPLES = 3600;
let arrTemperature = Array(SAMPLES).fill(0);
let arrHumidity = Array(SAMPLES).fill(0);
let preTemperature = 0;
let preHumidity = 0;
let sensingTempHumi = () => {
    sensor.read(22, 11, function (err, temperature, humidity) {
        if (!err) {
            console.log(`temp: ${temperature}°C, humidity: ${humidity}%`);

            if (local_mqtt_client) {
                local_mqtt_client.publish('/puleunair/temphumi', (temperature.toString() + ',' + humidity.toString()));
                crtci('PA1/temphumi', temperature.toString() + ',' + humidity.toString());

                arrTemperature.shift();
                arrTemperature.push(parseFloat(temperature));

                arrHumidity.shift();
                arrHumidity.push(parseFloat(humidity));

                preTemperature = parseFloat(temperature);
                preHumidity = parseFloat(humidity);
            }
        }
        else {
            if (local_mqtt_client) {
                local_mqtt_client.publish('/puleunair/temphumi', (preTemperature.toString() + ',' + preHumidity.toString()));
                crtci('PA1/temphumi', preTemperature.toString() + ',' + preHumidity.toString());

                arrTemperature.shift();
                arrTemperature.push(parseFloat(preTemperature));

                arrHumidity.shift();
                arrHumidity.push(parseFloat(preHumidity));
            }
        }

        setTimeout(sensingTempHumi, 2000);
    });

}

sensingTempHumi();

function crtci(url, con) {
    let data = {};
    data["m2m:cin"] = {};
    data["m2m:cin"].con = con;

    let config = {
        method: 'post',
        maxBodyLength: Infinity,
        url: 'http://121.137.228.240:7579/Mobius/PureunAir/' + url,
        headers: {
            'Accept': 'application/json',
            'X-M2M-RI': '12345',
            'X-M2M-Origin': 'SOrigin',
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
