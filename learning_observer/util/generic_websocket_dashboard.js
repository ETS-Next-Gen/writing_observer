/*
  This is test code for our new generic dashboard framework.

  It runs with node.js. We're developing it in node so that we can use
  this as a starting point for thinking about a front-end framework, and
  perhaps share test code.

  We don't have a clean plan for where we'll go (e.g. reuse code versus
  prototypes). It's starting as a clone of the Python code with the same
  filename.
*/

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

// We can comment in/out console.log(`d`) based on whether we want a giant amount of debug data
socket.onerror = function(d) { console.log("Error"); console.log(d); };
socket.onclose = function(d) { console.log("Close"); /* console.log(d); */ };
