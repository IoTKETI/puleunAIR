/**
 * Created by Wonseok Jung in KETI on 2023-02-10.
 */

const mqtt = require('mqtt');
const {nanoid} = require('nanoid');
const fs = require("fs");
const term = require('terminal-kit').terminal;

let local_mqtt_client = null;
const sub_watertemp_topic = '/puleunair/hotwater';
const sub_humidity_topic = '/puleunair/humidity';
const sub_temperature_topic = '/puleunair/temperature';

let hotwater_temp = 0.0;
let humidity = 0.0;
let temperature = 0.0;

local_mqtt_connect('127.0.0.1');

const control_items = ['Quit', 'Control_1', 'Control_2', 'Control_3', 'Control_4', 'Control_5', 'All', 'AUTO'];
const auto_items = ['Back', 'Heater', 'Air', 'Pump', 'Fan', 'Spray'];

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
            if (sub_temperature_topic !== '') {
                local_mqtt_client.subscribe(sub_temperature_topic);
                console.log('[local_mqtt] sub_temperature_topic is subscribed: ' + sub_temperature_topic);
            }
        });

        local_mqtt_client.on('message', function (topic, message) {
            if (topic === sub_watertemp_topic) {
                // console.log('sub_watertemp_topic - ', message.toString());
                hotwater_temp = message.toString();
            }

            else if (topic === sub_humidity_topic) {
                // console.log('sub_humidity_topic - ', message.toString());
                humidity = message.toString();
            }

            else if (topic === sub_temperature_topic) {
                // console.log('sub_temperature_topic - ', message.toString());
                temperature = message.toString();
            }
        });

        local_mqtt_client.on('error', function (err) {
            console.log('[local_mqtt] (error) ' + err.message);
            local_mqtt_client = null;
            local_mqtt_connect(serverip);
        });
    }
}

let startMenuIndex = 0;
let startMenuDroneSelected = 'none';
let cur_control_list_selected = [];
let cur_command_items = [];
let command_items = ['Back', 'ON', 'OFF'];
let startmenu_list = control_items;

function startMenu() {
    placeFlag = 'startMenu';

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


        if (startMenuDroneSelected === 'Quit') {
            process.exit();
        }
        else if (startMenuDroneSelected === 'AUTO') {
            cur_command_items = [].concat(auto_items);

            term('\n').eraseDisplayBelow();

            local_mqtt_client.publish('/puleunair/Control_3/set', '1', () => {
                // console.log('Send ON command to ' + control_selected);
            });

            elapsed_count = 0;
            spray_count = 0;
            air_count = 0;

            autoMenu();
        }
        else {
            cur_command_items = [].concat(command_items);

            if (startMenuDroneSelected === 'All') {
                cur_control_list_selected = [].concat(control_items);
            }
            else {
                cur_control_list_selected = [].concat(control_items[startMenuIndex]);
            }

            term('\n').eraseDisplayBelow();

            allMenu();
        }
    });
}

let elapsed_count = 0;
let spray_count = 0;
let air_count = 0;

let period = {};
let heater_period = 24.0; // temperature
let spray_period = 10; // minutes
let air_period = 10; // minutes
let fan_period = 90;

let args = process.argv;
let profile_name = 'Profile.json';

if(args.hasOwnProperty('2')) {
    profile_name = args[2];
}

try {
    period = JSON.parse(fs.readFileSync(profile_name, 'utf8'));

    heater_period = period.heater_period;
    spray_period = period.spray_period;
    air_period = period.air_period;
    fan_period = period.fan_period;
} catch (e) {
    period.heater_period = heater_period;
    period.spray_period = spray_period;
    period.air_period = air_period;
    period.fan_period = fan_period;

    fs.writeFileSync(profile_name, JSON.stringify(period, null, 4), 'utf8');
}

setInterval(() => {
    term.moveTo.green(1, 2, "                                                                                    ");
    term.moveTo.green(1, 3, "                                                                                    ");
    term.moveTo.green(1, 4, "                                                                                    ");
    term.moveTo.green(1, 5, "                                                                                    ");

    term.moveTo.green(1, 3, "          Temperature: %s*C", parseFloat(temperature).toFixed(1));
    term.moveTo.green(1, 4, "             Humidity: %s\%", parseFloat(humidity).toFixed(1));
    term.moveTo.green(1, 5, " Hotwater Temperature: %s*C\n", hotwater_temp);

    if(parseFloat(hotwater_temp) < heater_period) {
        local_mqtt_client.publish('/puleunair/Control_1/set', '1', () => {
            // console.log('Send ON command to ' + control_selected);
        });
    }
    else if(parseFloat(hotwater_temp) > (heater_period + 0.4)) {
        local_mqtt_client.publish('/puleunair/Control_1/set', '0', () => {
            // console.log('Send ON command to ' + control_selected);
        });
    }
}, 1000);

setInterval(() => {
    // elapsed_count++;
    //
    // term.moveTo.green(1, 6, "                                                                                    ");
    // term.moveTo.green(1, 7, "                                                                                    ");
    // term.moveTo.green(1, 8, "                                                                                    ");
    // term.moveTo.green(1, 9, "                                                                                    ");
    // term.moveTo.green(1, 10, "                                                                                    ");
    // term.moveTo.green(1, 11, "                                                                                    ");
    // term.moveTo.green(1, 12, "                                                                                    ");

    if(placeFlag === 'autoMenu') {
        period.auto = 1;

        local_mqtt_client.publish('/puleunair/auto/set', JSON.stringify(period), () => {
            console.log('Send AUTO command to /puleunair/auto/set');
        });

        // term.moveTo.green(1, 7,  " AUTO MODE\n");
        // term.moveTo.green(1, 8,  "     HEATER: < %f*C\n", heater_period);
        // term.moveTo.green(1, 9,  "        AIR: %d minutes per hour\n", air_period);
        // term.moveTo.green(1, 10,  "       PUMP: always on\n");
        // term.moveTo.green(1, 11, "        FAN: > %f%\n", fan_period);
        // term.moveTo.green(1, 12, "      SPRAY: %d minutes per hour\n", spray_period);
        //
        // if(parseFloat(humidity) > fan_period) {
        //     local_mqtt_client.publish('/puleunair/Control_4/set', '1', () => {
        //         // console.log('Send ON command to ' + control_selected);
        //     });
        // }
        // else if(parseFloat(humidity) < (fan_period - 5)) {
        //     local_mqtt_client.publish('/puleunair/Control_4/set', '0', () => {
        //         // console.log('Send ON command to ' + control_selected);
        //     });
        // }
        //
        // spray_count++;
        // if (0 <= spray_count && spray_count < (spray_period * 60)) {
        //     local_mqtt_client.publish('/puleunair/Control_5/set', '1', () => {
        //         // console.log('Send ON command to ' + control_selected);
        //     });
        // }
        // else if ((spray_period * 60) <= spray_count && spray_count < (60 * 60)) {
        //     local_mqtt_client.publish('/puleunair/Control_5/set', '0', () => {
        //         // console.log('Send ON command to ' + control_selected);
        //     });
        // }
        // else {
        //     spray_count = 0;
        // }
        //
        //
        // air_count++;
        // if (0 <= air_count && air_count < (air_period * 60)) {
        //     local_mqtt_client.publish('/puleunair/Control_2/set', '1', () => {
        //         // console.log('Send ON command to ' + control_selected);
        //     });
        // }
        // else if ((air_period * 60) <= air_count && air_count < (60 * 60)) {
        //     local_mqtt_client.publish('/puleunair/Control_2/set', '0', () => {
        //         // console.log('Send ON command to ' + control_selected);
        //     });
        // }
        // else {
        //     air_count = 0;
        // }
    } else {
        period.auto = 0;

        local_mqtt_client.publish('/puleunair/auto/set', JSON.stringify(period), () => {
            console.log('Send AUTO command to /puleunair/auto/set');
        });
    }
}, 1000);

let placeFlag = '';
let printFlag = '';
let curAllMenuIndex = 0;
const back_menu_delay = 100;

function autoMenu() {
    placeFlag = 'autoMenu';
    printFlag = 'enable';

    let _options = {
        y: 1,	// the menu will be on the top of the terminal
        style: term.inverse,
        selectedStyle: term.dim.blue.bgGreen,
        selectedIndex: curAllMenuIndex
    };

    term.singleLineMenu(cur_command_items, _options, function (error, response) {
        term('\n').eraseLineAfter.moveTo.green(1, 2,
            "#%s selected: %s (%s,%s)\n",
            response.selectedIndex,
            response.selectedText,
            response.x,
            response.y
        );

        curAllMenuIndex = response.selectedIndex;

        if (startMenuDroneSelected === 'All') {
            cur_control_list_selected = [].concat(control_items);
        }
        else {
            cur_control_list_selected = [].concat(control_items[startMenuIndex]);
        }

        if (response.selectedText === 'Back') {
            setTimeout(startMenu, back_menu_delay);
        }
        else {
            setTimeout(startMenu, back_menu_delay);
        }
    });
}

function allMenu() {
    placeFlag = 'allMenu';
    printFlag = 'enable';

    let _options = {
        y: 1,	// the menu will be on the top of the terminal
        style: term.inverse,
        selectedStyle: term.dim.blue.bgGreen,
        selectedIndex: curAllMenuIndex
    };

    term.singleLineMenu(cur_command_items, _options, function (error, response) {
        term('\n').eraseLineAfter.moveTo.green(1, 2,
            "#%s selected: %s (%s,%s)\n",
            response.selectedIndex,
            response.selectedText,
            response.x,
            response.y
        );

        curAllMenuIndex = response.selectedIndex;

        if (startMenuDroneSelected === 'All') {
            cur_control_list_selected = [].concat(control_items);
        }
        else {
            cur_control_list_selected = [].concat(control_items[startMenuIndex]);
        }

        if (response.selectedText === 'Back') {
            setTimeout(startMenu, back_menu_delay);
        }
        else if (response.selectedText === 'ON') {
            allOnMenu();
        }
        else if (response.selectedText === 'OFF') {
            allOffMenu();
        }
        else {
            setTimeout(startMenu, back_menu_delay);
        }
    });
}

function allOnMenu() {
    term.eraseDisplayBelow();
    term.moveTo.red(1, 3, '');

    for (let idx in cur_control_list_selected) {
        if (cur_control_list_selected.hasOwnProperty(idx)) {
            let control_selected = cur_control_list_selected[idx];

            if (control_selected.includes('Control')) {
                if (local_mqtt_client !== null) {
                    local_mqtt_client.publish('/puleunair/' + control_selected + '/set', '1', () => {
                        // console.log('Send ON command to ' + control_selected);
                    });
                }
            }
        }
    }

    setTimeout(allMenu, back_menu_delay * (cur_control_list_selected.length + 1));
}

function allOffMenu() {
    term.eraseDisplayBelow();
    term.moveTo.red(1, 3, '');

    for (let idx in cur_control_list_selected) {
        if (cur_control_list_selected.hasOwnProperty(idx)) {
            let control_selected = cur_control_list_selected[idx];

            if (control_selected.includes('Control')) {
                if (local_mqtt_client !== null) {
                    local_mqtt_client.publish('/puleunair/' + control_selected + '/set', '0', () => {
                        // console.log('Send OFF command to ' + control_selected);
                    });
                }
            }
        }
    }
    setTimeout(allMenu, back_menu_delay * (cur_control_list_selected.length + 1));
}

setTimeout(startMenu, 1000);
