// var d3 = require('d3');
// d3.text("https://www.google.com", function(d) {console.log(d);});
const WebSocket = require('ws');

server = 'ws://localhost:8888/wsapi/generic_dashboard'

messages = [
    {
        "action": "subscribe",
        "keys": [{
            "source" : "da_timeline.visualize.handle_event",
            "KeyField.STUDENT": "guest-225d890e93a6b04c0aefe515b9d2dac9"
        }],
        "refresh": [0.5, "seconds"]
    },
    {
        "action": "subscribe",
        "keys":  [{
            "source" : "da_timeline.visualize.handle_event",
            "KeyField.STUDENT": "INVALID-STUDENT"
        }],
        "refresh": [2, "seconds"]
    },
    {
        "action": "start"
    }
]

socket = new WebSocket(server);
socket.on('message', msg => console.log(msg.toString()));

socket.onopen = function() {
    console.log("Open");
    for(var i=0; i<messages.length; i++) {
	socket.send(JSON.stringify(messages[i]));
    }
};

// We can comment in `d` if we want a giant amount of debug data
socket.onerror = function(d) { console.log("Error"); /* console.log(d); */ };
socket.onclose = function(d) { console.log("Close"); /* console.log(d); */ };
