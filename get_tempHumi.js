
const sensor = require("node-dht-sensor");
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

            local_mqtt_client.subscribe('/puleunair/req/arrAutoTemperature');
            local_mqtt_client.subscribe('/puleunair/req/arrAutoHumidity');
        });

        local_mqtt_client.on('message', (topic, message) => {
            if (topic === '/puleunair/req/arrAutoTemperature') {
                local_mqtt_client.publish('/puleunair/res/arrAutoTemperature', JSON.stringify(arrTemperature));
            }
            else if (topic === '/puleunair/req/arrAutoHumidity') {
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

let sensingTempHumi = () => {
    sensor.read(22, 11, function(err, temperature, humidity) {
        if (!err) {
            console.log(`temp: ${temperature}°C, humidity: ${humidity}%`);

            if(local_mqtt_client) {
                local_mqtt_client.publish('/puleunair/temphumi', (temperature.toString()+','+humidity.toString()));
//TODO: cin 생성
                arrTemperature.shift();
                arrTemperature.push(parseFloat(temperature));

                arrHumidity.shift();
                arrHumidity.push(parseFloat(humidity));
            }
        }

        setTimeout(sensingTempHumi, 2000);
    });

}

sensingTempHumi();
