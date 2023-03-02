const fs = require("fs");
const {nanoid} = require("nanoid");
const mqtt = require("mqtt");
const axios = require('axios');

const pureunHost = 'gcs.iotocean.org';

let crt_cin = (url, con) => {
    let data = {};
    data["m2m:cin"] = {};
    data["m2m:cin"].con = con;

    let config = {
        method: 'post',
        maxBodyLength: Infinity,
        url: 'http://'+pureunHost+':7579/Mobius/PureunAir/' + url,
        headers: {
            'Accept': 'application/json',
            'X-M2M-RI': '12345',
            'X-M2M-Origin': 'SOrigin',
            'Content-Type': 'application/json; ty=4'
        },
        data: data
    };

    axios(config).then((response) => {
        // console.log(JSON.stringify(response.data));
    })
    .catch((error) => {
        console.log(error);
    });
}

let local_mqtt_client = null;
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

            local_mqtt_client.subscribe('/puleunair/temphumi');
            local_mqtt_client.subscribe('/puleunair/hotwater');
            local_mqtt_client.subscribe('/puleunair/status');
        });

        local_mqtt_client.on('message', (topic, message) => {
            if (topic === '/puleunair/temphumi') {
                let arrVal = message.toString().split(',');
                curTemperature = parseFloat(arrVal[0]).toFixed(1);
                curHumidity = parseFloat(arrVal[1]).toFixed(1);
            }
            else if (topic === '/puleunair/hotwater') {
                let arrVal = message.toString().split(',');
                curHotwater = parseFloat(arrVal[0]).toFixed(1);
            }
            else if (topic === '/puleunair/status') {
                let objVal = JSON.parse(message.toString());

                ctrlHeater = objVal.ctrl1;
                ctrlAir = objVal.ctrl2;
                ctrlPump = objVal.ctrl3;
                ctrlFan = objVal.ctrl4;
                ctrlSpray = objVal.ctrl5;
            }
        });

        local_mqtt_client.on('error', (err) => {
            console.log('[local_mqtt] (error) ' + err.message);
            local_mqtt_client = null;
            local_mqtt_connect(serverip);
        });
    }
}

let pureun_mqtt_client = null;
function pureun_mqtt_connect(serverip) {
    if (pureun_mqtt_client === null) {
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

        pureun_mqtt_client = mqtt.connect(connectOptions);

        pureun_mqtt_client.on('connect', () => {
            console.log('local_mqtt is connected to ( ' + serverip + ' )');

            pureun_mqtt_client.subscribe('/puleunair/auto/set');

            pureun_mqtt_client.subscribe('/puleunair/req/arrAutoTemperature');
            pureun_mqtt_client.subscribe('/puleunair/req/arrAutoHumidity');
            pureun_mqtt_client.subscribe('/puleunair/req/arrAutoHotwater');
            pureun_mqtt_client.subscribe('/puleunair/req/arrAutoHeater');
            pureun_mqtt_client.subscribe('/puleunair/req/arrAutoFan');
        });

        pureun_mqtt_client.on('message', (topic, message) => {
            if(topic === '/puleunair/auto/set') {
                let objVal = JSON.parse(message.toString());
                autoMode = objVal.auto;
                heater_period = objVal.heater_period;
                air_period = objVal.air_period;
                fan_period = objVal.fan_period;
                spray_period = objVal.spray_period;
                heater_offset = objVal.heater_offset;
                fan_offset = objVal.fan_offset;

                if(autoMode) {
                    air_count = 0;
                    spray_count = 0;

                    period.auto = autoMode;
                    period.heater_period = heater_period;
                    period.air_period = air_period;
                    period.fan_period = fan_period;
                    period.spray_period = spray_period;
                    period.heater_offset = heater_offset;
                    period.fan_offset = fan_offset;
                    fs.writeFileSync('Profile.json', JSON.stringify(period, null, 4), 'utf8');
                }
            }
            else if (topic === '/puleunair/req/arrAutoTemperature') {
                pureun_mqtt_client.publish('/puleunair/res/arrAutoTemperature', JSON.stringify(arrTemperature));
            }
            else if (topic === '/puleunair/req/arrAutoHumidity') {
                pureun_mqtt_client.publish('/puleunair/res/arrAutoHumidity', JSON.stringify(arrHumidity));
            }
            else if (topic === '/puleunair/req/arrAutoHotwater') {
                pureun_mqtt_client.publish('/puleunair/res/arrAutoHotwater', JSON.stringify(arrHotwater));
            }
            else if (topic === '/puleunair/req/arrAutoHeater') {
                pureun_mqtt_client.publish('/puleunair/res/arrAutoHeater', JSON.stringify(arrHeater));
            }
            else if (topic === '/puleunair/req/arrAutoFan') {
                pureun_mqtt_client.publish('/puleunair/res/arrAutoFan', JSON.stringify(arrFan));
            }
        });

        pureun_mqtt_client.on('error', (err) => {
            console.log('[local_mqtt] (error) ' + err.message);
            pureun_mqtt_client = null;
            pureun_mqtt_connect(serverip);
        });
    }
}

let curTemperature = 0;
let curHumidity = 0;
let curHotwater = 0;

let ctrlHeater = 0;
let ctrlAir = 0;
let ctrlPump = 0;
let ctrlFan = 0;
let ctrlSpray = 0;

let autoMode = 0;
let heater_period = 22.0;
let air_period = 5;
let fan_period = 70.0;
let spray_period = 1;
let heater_offset = 0.2;
let fan_offset = 3;

const SAMPLES = 3600;
let arrTemperature = Array(SAMPLES).fill(0);
let arrHumidity = Array(SAMPLES).fill(0);
let arrHotwater = Array(SAMPLES).fill(0);
let arrHeater = Array(SAMPLES).fill(0);
let arrFan = Array(SAMPLES).fill(0);
let air_count = 0;
let spray_count = 0;

let period = {};
try {
    period = JSON.parse(fs.readFileSync('Profile.json', 'utf8'));

    autoMode = period.auto;
    heater_period = period.heater_period;
    air_period = period.air_period;
    fan_period = period.fan_period;
    spray_period = period.spray_period;
    heater_offset = period.heater_offset;
    fan_offset = period.fan_offset;
}
catch (e) {
    period.auto = autoMode;
    period.heater_period = heater_period;
    period.spray_period = spray_period;
    period.air_period = air_period;
    period.fan_period = fan_period;
    period.heater_offset = heater_offset;
    period.fan_offset = fan_offset;
    fs.writeFileSync('Profile.json', JSON.stringify(period, null, 4), 'utf8');
}

let autoMonitor = () => {
    setInterval(() => {
        if(parseFloat(curHotwater) < parseFloat(heater_period)) {
            local_mqtt_client.publish('/puleunair/Control_1/set', '1');
        }
        else if(parseFloat(curHotwater) > (parseFloat(heater_period) + parseFloat(heater_offset))) {
            local_mqtt_client.publish('/puleunair/Control_1/set', '0');
        }

        if(autoMode === 1) {
            if(parseFloat(curHumidity) > parseFloat(fan_period)) {
                local_mqtt_client.publish('/puleunair/Control_4/set', '1');
            }
            else if(parseFloat(curHumidity) < (parseFloat(fan_period) - parseFloat(fan_offset))) {
                local_mqtt_client.publish('/puleunair/Control_4/set', '0');
            }

            air_count++;
            if (0 <= air_count && air_count < (parseInt(air_period) * 60)) {
                local_mqtt_client.publish('/puleunair/Control_2/set', '1');
            }
            else if ((parseInt(air_period) * 60) <= air_count && air_count < (60 * 60)) {
                local_mqtt_client.publish('/puleunair/Control_2/set', '0');
            }
            else {
                air_count = 0;
            }

            local_mqtt_client.publish('/puleunair/Control_3/set', '1');

            spray_count++;
            if (0 <= spray_count && spray_count < (parseInt(spray_period) * 60)) {
                local_mqtt_client.publish('/puleunair/Control_5/set', '1');
            }
            else if ((parseInt(spray_period) * 60) <= spray_count && spray_count < (60 * 60)) {
                local_mqtt_client.publish('/puleunair/Control_5/set', '0');
            }
            else {
                spray_count = 0;
            }
        }
    }, 1000);
}

let status = {};
let sendStatus = () => {
    setInterval(() => {
        status.auto = autoMode;
        status.heater_period = heater_period;
        status.spray_period = spray_period;
        status.air_period = air_period;
        status.fan_period = fan_period;
        status.heater_offset = heater_offset;
        status.fan_offset = fan_offset;
        status.ctrlHeater = ctrlHeater;
        status.ctrlAir = ctrlAir;
        status.ctrlPump = ctrlPump;
        status.ctrlFan = ctrlFan;
        status.ctrlSpray = ctrlSpray;
        status.curTemperature = curTemperature;
        status.curHumidity = curHumidity;
        status.curHotwater = curHotwater;

        arrHotwater.shift();
        arrHotwater.push(parseFloat(curHotwater));
        arrTemperature.shift();
        arrTemperature.push(parseFloat(curTemperature));
        arrHumidity.shift();
        arrHumidity.push(parseFloat(curHumidity));
        arrHeater.shift();
        arrHeater.push(ctrlHeater);
        arrFan.shift();
        arrFan.push(ctrlFan);

        pureun_mqtt_client.publish('/puleunair/status', JSON.stringify(status));

        crt_cin("PA1/status", JSON.stringify(status))
    }, 2000);
}

local_mqtt_connect('localhost');
pureun_mqtt_connect(pureunHost);

setTimeout(()=>{
    autoMonitor();
}, 1000);

setTimeout(()=>{
    sendStatus();
}, 2000);

