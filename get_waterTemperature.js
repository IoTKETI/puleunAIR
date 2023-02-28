
const sensor = require('ds18b20-raspi');
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
let preTempC = 0;

let sensingWaterTemperature = () => {
    const tempC = sensor.readSimpleC(1);
    if(tempC) {
        console.log('Water Temperature: ' + `${tempC} degC`);

        if(local_mqtt_client) {
            local_mqtt_client.publish('/puleunair/hotwater', tempC.toString());
            crtci('PA1/hotwater', tempC.toString());

            arrHotwater.shift();
            arrHotwater.push(parseFloat(tempC));

            preTempC = parseFloat(tempC);
        }
    }
    else {
        if (local_mqtt_client) {
            local_mqtt_client.publish('/puleunair/hotwater', preTempC.toString());
            crtci('PA1/hotwater', preTempC.toString());

            arrHotwater.shift();
            arrHotwater.push(parseFloat(preTempC));
        }
    }

    //setTimeout(sensingWaterTemperature, 2000);
}

//sensingWaterTemperature();

setInterval(sensingWaterTemperature, 2000);

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
