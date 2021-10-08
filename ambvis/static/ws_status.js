var testsock = new WebSocket('ws://ambvis.molbio.slu.se:8080/api/ws');
var xhr = new XMLHttpRequest();
var system_status;

var spinner;
var move_num;
var led;
var motor_pos;
var status_text;

document.addEventListener('DOMContentLoaded', function() {
    spinner = document.getElementById('spinner');
    spinner.style['display'] = 'none';
    move_num = document.getElementById('move');
    led = document.getElementById('led_checkbox');
    motor_pos = document.getElementById('motor_position');
    status_text = document.getElementById('response');
}, false);

testsock.onmessage = function (event) {
    console.log(event.data);
    var prev_status = system_status;
    system_status = JSON.parse(event.data);
    if (system_status != prev_status) {
        update_status();
    }
}

function update_status() {
    led.value = system_status.led;
    motor_pos.innerHTML = system_status.position;
}

function bg_get(url) {
    xhr.open('GET', url);
    xhr.send();
}

function toggle_led(value) {
    if(value) {
        bg_get('/led/on');
    } else {
        bg_get('/led/off');
    }
}

function move_rel() {
    spinner.style['display'] = 'block';
    bg_get('/motor/move/rel/' + move_num.value);
    xhr.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            spinner.style['display'] = 'none';
            status_text.innerHTML = xhr.responseText;
        }
    };
}

function move_abs() {
    spinner.style['display'] = 'block';
    bg_get('/motor/move/abs/' + move_num.value);
    xhr.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            spinner.style['display'] = 'none';
            status_text.innerHTML = xhr.responseText;
        }
    };
}
