/**
 * Created by Wonseok Jung in KETI on 2023-02-10.
 */

const mqtt = require('mqtt');
const {nanoid} = require('nanoid');
const term = require('terminal-kit').terminal;

let local_mqtt_client = null;
const sub_watertemp_topic = '/puleunair/hotwater/res';
const sub_humidity_topic = '/puleunair/humi/res';
const pub_watertemp_topic = '/puleunair/hotwater/req';
const pub_humidity_topic = '/puleunair/humi/req';
const set_Control_1_topic = '/puleunair/Control1/set';
const set_Control_2_topic = '/puleunair/Control2/set';
const set_Control_3_topic = '/puleunair/Control3/set';
const set_Control_4_topic = '/puleunair/Control4/set';
const set_Control_5_topic = '/puleunair/Control5/set';

let hotwater_temp = 0.0;
let humidity = 0.0;

local_mqtt_connect('127.0.0.1');

let startmenu_list = ['Quit', 'Control_1', 'Control_2', 'Control_3', 'Control_4', 'Control_5', 'All'];

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
            term.clear();

            if (sub_watertemp_topic !== '') {
                local_mqtt_client.subscribe(sub_watertemp_topic);
                console.log('[local_mqtt] sub_watertemp_topic is subscribed: ' + sub_watertemp_topic);
            }
            if (sub_humidity_topic !== '') {
                local_mqtt_client.subscribe(sub_humidity_topic);
                console.log('[local_mqtt] sub_humidity_topic is subscribed: ' + sub_humidity_topic);
            }
        });

        local_mqtt_client.on('message', function (topic, message) {
            if (topic === sub_watertemp_topic) {
                console.log('sub_watertemp_topic - ', message.toString());
                hotwater_temp = message.toString();
            }

            if (topic === sub_humidity_topic) {
                console.log('sub_humidity_topic - ', message.toString());
                humidity = message.toString();
            }
        });

        local_mqtt_client.on('error', function (err) {
            console.log('[local_mqtt] (error) ' + err.message);
            local_mqtt_client = null;
            local_mqtt_connect(serverip);
        });
    }
}

function req_watertemp() {
    if (local_mqtt_client !== null) {
        local_mqtt_client.publish(pub_watertemp_topic, 'req');
    }
}

function req_humidity() {
    if (local_mqtt_client !== null) {
        local_mqtt_client.publish(pub_humidity_topic, 'req');
    }
}

setInterval(req_watertemp, 1000);
setInterval(req_humidity, 1000);

function set_control(point, val) {
    if (local_mqtt_client !== null) {
        local_mqtt_client.publish(eval('set_Control_' + point + '_topic'))
    }
}

let startMenuIndex = 0;
let startMenuDroneSelected = 'none';
let cur_goto_position = 'none';
let cur_mode_selected = 'none';
let cur_drone_list_selected = [];
let cur_command_items = [];
let command_items = ['Back', 'ON', 'OFF'];

function startMenu() {
    let _options = {
        y: 1,	// the menu will be on the top of the terminal
        style: term.inverse,
        selectedStyle: term.dim.yellow.bgGray,
        selectedIndex: startMenuIndex
    };

    term.singleLineMenu(startmenu_list, _options, function (error, response) {
        term('\n').eraseLineAfter.moveTo.green(1, 2,
            "#%s selected: %s (%s,%s)\n",
            response.selectedIndex,
            response.selectedText,
            response.x,
            response.y
        );

        startMenuDroneSelected = response.selectedText;
        startMenuIndex = response.selectedIndex;

        // console.log(response);

        cur_command_items = [].concat(command_items);

        if (startMenuDroneSelected === 'All') {
            cur_drone_list_selected = [].concat(conf.drone);

            cur_command_items.splice(cur_command_items.indexOf('Follow'), 1);
            //cur_command_items.splice(cur_command_items.indexOf('Real_Control'), 1);
        } else if (startMenuDroneSelected === 'Quit') {
            process.exit();
        } else {
            cur_drone_list_selected = [].concat(conf.drone[startMenuIndex - 1]);
        }
        //
        // term('\n').eraseDisplayBelow();
        //
        // allMenu();
    });
}

// setTimeout(startMenu, 1000);
