
const sensor = require('ds18b20-raspi');
const {nanoid} = require("nanoid");
const mqtt = require("mqtt");

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

            local_mqtt_client.subscribe('/puleunair/req/arrAutoHotwater');
        });

        local_mqtt_client.on('message', (topic, message) => {
            if (topic === '/puleunair/req/arrAutoHotwater') {
                local_mqtt_client.publish('/puleunair/res/arrAutoHotwater', JSON.stringify(arrHotwater));
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
let arrHotwater = Array(SAMPLES).fill(0);

let sensingWaterTemperature = () => {
    const tempC = sensor.readSimpleC(1);
    console.log('Water Temperature: ' + `${tempC} degC`);

    if(local_mqtt_client) {
        local_mqtt_client.publish('/puleunair/hotwater', tempC.toString());

        arrHotwater.shift();
        arrHotwater.push(parseFloat(tempC));
    }

    setTimeout(sensingWaterTemperature, 2000);
}

sensingWaterTemperature();

