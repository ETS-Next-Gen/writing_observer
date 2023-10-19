/*
Background script. This works across all of Google Chrome.
*/

// Do not save debug requests. We flip this frequently. Perhaps this
// should be a cookie or browser.storage?
var RAW_DEBUG = false;

/* This variable must be manually updated to specify the server that
 * the data will be sent to.  
*/
var WEBSOCKET_SERVER_URL = "wss://learning-observer.org/wsapi/in/" 

import { googledocs_id_from_url } from './writing_common';

import * as lo_event from 'lo_event';

const loggers = [
  lo_event.consoleLogger,
  lo_event.websocketLogger(WEBSOCKET_SERVER_URL)
]

lo_event.init('org.mitros.writing', '0.01', loggers, '', '')
lo_event.setFieldSet([{ test: 'this is a test' }])
lo_event.go()
/*
  TODO: FSM

  +----------------------+
  | Load server settings |
  | from chrome.storage  |
  +----------------------+
            |
            v
  +-------------------+
  | Connect to server |
  +-------------------+

    Load events queue
   from chrome.storage


Dequeue events
*/

function profileInfoWrapper(callback) {
    /* Workaround for this bug:
       https://bugs.chromium.org/p/chromium/issues/detail?id=907425#c6
     */
    try {
        chrome.identity.getProfileUserInfo({accountStatus: 'ANY'}, callback);
    } catch (e) {
        // accountStatus not supported
        chrome.identity.getProfileUserInfo(callback);
    }
}

function console_logger() {
    /*
      Log to browser JavaScript console
     */
    return console.log;
}


function add_event_metadata(event_type, event) {
    /*
      TODO: Should we add user identity?
     */
    event['event'] = event_type;

    // Add the event_type if not present
    if (!event.hasOwnProperty('event_type')) {
        event['event_type'] = event_type;
    }

    event['source'] = 'org.mitros.writing_analytics';
    event['version'] = 'alpha';
    event['ts'] = Date.now();
    event['human_ts'] = Date();
    event['iso_ts'] = new Date().toISOString;
    return event;
}


function websocket_logger(server) {
    /*
       Log to web socket server.

       Optional:
       * We could send queued events on socket open (or on a timeout)
       * Or we could just wait for the next event (what we do now)

       The former would be a little bit more robust.
    */
    var socket;
    var state = new Set()
    var queue = [];

    function new_websocket() {
        socket = new WebSocket(server);
        socket.onopen=prepare_socket;
        socket.onerror = function(event) {
            console.log("Could not connect");
            var event = { "issue": "Could not connect" };
            event = add_event_metadata("warning", event);
            event = JSON.stringify(event);
            queue.push(event);
        };
        socket.onclose = function(event) {
            console.log("Lost connection");
            var event = { "issue": "Lost connection", "code": event.code };
            event = add_event_metadata("warning", event);
            event = JSON.stringify(event);
            queue.push(event);
        };
        return socket;
    }

    socket = new_websocket();

    function are_we_done() {
        if (state.has("chrome_identity") &&
            state.has("local_storage")) {
            var event = {};
            event = add_event_metadata('metadata_finished', event);
            socket.send(JSON.stringify(event));
            state.add("ready");
        }
    }

    function prepare_socket() {
        // Send the server the user info. This might not always be available.
        state = new Set();
        let event;
        profileInfoWrapper(function callback(userInfo) {
            event = {
                "chrome_identity": userInfo
            };
            event = add_event_metadata("chrome_identity", event);
            socket.send(JSON.stringify(event));
            state.add("chrome_identity");
            are_we_done();
        });
        let storage_keys = [
            "teacher_tag", // Unused. In the future: whom do we authorize to receive data?
            "user_tag", // Unique per-user tag in the settings page
            "process_server", // Unused. Which server should we send to?
            "unique_id", // Unique ID set in the settings page
            "generated_id" // Autogenerated, for future forensics
        ]
        chrome.storage.sync.get(storage_keys, function(result) {
            if(result !== undefined) {
                event = {'local_storage': result};
            } else {
                event = {'local_storage': {}};
            }
            /*if("generated_id" not in event['local_storage']){
                event['local_storage']['generated_id'] = unique_id();
                chrome.storage.sync.set(
                    'generated_id',
                    event['local_storage']['generated_id']
                );
            }*/
            console.log(event);
            event = add_event_metadata("local_storage", event);
            console.log(event);
            socket.send(JSON.stringify(event));
            state.add("local_storage");
            are_we_done();
        });
    }

    function dequeue() {
        if(socket === null) {
            // Do nothing. We're reconnecting.
            console.log("Event squelched; reconnecting");
        } else if(socket.readyState === socket.OPEN &&
           state.has("ready")) {
            while(queue.length > 0) {
                var event = queue.shift();
                socket.send(event);  /* TODO: We should do receipt confirmation before dropping events */
            }
        } else if((socket.readyState == socket.CLOSED) || (socket.readyState == socket.CLOSING)) {
            /*
              If we lost the connection, we wait a second and try to open it again.

              Note that while socket is `null` or `CONNECTING`, we don't take either
              branch -- we just queue up events. We reconnect after 1 second if closed,
              or dequeue events if open.
            */
            console.log("Re-opening connection in 1s");
            socket = null;
            state = new Set();
            setTimeout(function() {
                console.log("Re-opening connection");
                socket = new_websocket();
            }, 1000);
        }
    }

    return function(data) {
        queue.push(data);
        dequeue();
    }
}

function ajax_logger(ajax_server) {
    /*
      HTTP event per request.

      To do: Handle failures / dropped connections
     */
    var server = ajax_server;
    return function (data) {
        /*
          Helper function to send a logging AJAX request to the server.
          This function takes a JSON dictionary of data.
        */

        httpRequest = new XMLHttpRequest();
        //httpRequest.withCredentials = true;
        httpRequest.open("POST", ajax_server);
        httpRequest.send(data);
    }
}

/*
List of loggers. For example, if we want to send to the server twice, and log on console:

loggers_enabled = [
    console_logger(),
    ajax_logger("https://localhost/webapi/"),
    websocket_logger("wss://localhost/wsapi/in/")
];
*/

let loggers_enabled = [
    console_logger(),
    //ajax_logger("https://writing.learning-observer.org/webapi/")//,


    // Adapted to NCSU Setup.
    // websocket_logger(WEBSOCKET_SERVER_URL)
    // websocketLogger(WEBSOCKET_SERVER_URL, chrome.storage.sync)
];

function log_event(event_type, event) {
    /*
       This sends an event to the server.
    */
    event = add_event_metadata(event_type, event);

    if(event['wa_source'] = null) {
        event['wa_source'] = 'background_page';
    }
    var json_encoded_event = JSON.stringify(event);

    for (var i=0; i<loggers_enabled.length; i++) {
        loggers_enabled[i](json_encoded_event);
    }
}

// Function to serve as replacement for 
// chrome.extension.getBackgroundPage().console.log(event); because it is not allowed in V3
// It logs the event to the console for debugging.
function logFromServiceWorker(event) {
  console.log(event);
}

function send_chrome_identity() {
  /*
       We sometimes may want to log the user's identity, as stored in
       Google Chrome. Note that this is not secure; we need oauth to do
       that. oauth can be distracting in that (at least in the workflow
       we used), it requires the user to confirm permissions.

       Perhaps want to do oauth exactly once per device, and use a
       unique token stored as a cookie or in browser.storage?

       Note this function is untested, following a refactor.
    */
  chrome.identity.getProfileInfo(function (userInfo) {
    lo_event.logEvent("chrome_identity_load", {
      email: userInfo.email,
      id: userInfo.id,
    });
  });
}

function this_a_google_docs_save(request) {
    /*
       Check if this is a Google Docs save request. Return true for something like:
       https://docs.google.com/document/d/1lt_lSfEM9jd7Ga6uzENS_s8ZajcxpE0cKuzXbDoBoyU/save?id=dfhjklhsjklsdhjklsdhjksdhkjlsdhkjsdhsdkjlhsd&sid=dhsjklhsdjkhsdas&vc=2&c=2&w=2&smv=2&token=lasjklhasjkhsajkhsajkhasjkashjkasaajhsjkashsajksas&includes_info_params=true
       And false otherwise.

       Note that while `save` is often early in the URL, on the first
       few requests of a web page load, it can be towards the end. We
       went from a conservative regexp to a liberal one. We should
       confirm this never catches extra requests, though.
    */
    if(request.url.match(/.*:\/\/docs\.google\.com\/document\/(.*)\/save/i)) {
        return true;
    }
    return false;
}

function this_a_google_docs_bind(request) {
    /*
      These request correspond to some server-push features, such as collaborative
      editing. We still need to reverse-engineer these.

      Note that we cannot monitor request responses without more
      complex JavaScript. See:

      https://stackoverflow.com/questions/6831916/is-it-possible-to-monitor-http-traffic-in-chrome-using-an-extension#6832018
    */
    if(request.url.match(/.*:\/\/docs\.google\.com\/document\/(.*)\/bind/i)) {
        return true;
    }
    return false;
}

// Figure out the system settings. Note this is asynchronous, so we
// chain dequeue_events when this is done.
/*
var WRITINGJS_AJAX_SERVER = null;

chrome.storage.sync.get(['process_server'], function(result) {
    //WRITINGJS_AJAX_SERVER = result['process_server'];
    if(!WRITINGJS_AJAX_SERVER) {
        WRITINGJS_AJAX_SERVER = "https://writing.learning-observer.org/webapi/";
    }
    dequeue_events();
});*/

// Listen for the keystroke messages from the page script and forward to the server.
chrome.runtime.onMessage.addListener(
    function(request, sender, sendResponse) {
        //chrome.extension.getBackgroundPage().console.log("Got message");
        //chrome.extension.getBackgroundPage().console.log(request);
        //console.log(sender);
        request['wa_source'] = 'client_page';
        lo_event.logEvent(request['event'], request);
    }
);

// Listen for web loads, and forward relevant ones (e.g. saves) to the server.
chrome.webRequest.onBeforeRequest.addListener(
    /*
      This allows us to log web requests. There are two types of web requests:
      * Ones we understand (SEMANTIC)
      * Ones we don't (RAW/DEBUG)

      There is an open question as to how we ought to handle RAW/DEBUG
      events. We will reduce potential issues around collecting data
      we don't want (privacy, storage, bandwidth) if we silently drop
      these. On the other hand, we significantly increase risk of
      losing user data should Google ever change their web API. If we
      log everything, we have good odds of being able to
      reverse-engineer the new API, and reconstruct what happened.

      Our current strategy is to:
      * Log the former requests in a clean way, extracting the data we
        want
      * Have a flag to log the debug requests (which includes the
        unparsed version of events we want).
      We should step through and see how this code manages failures,

      For development purposes, both modes of operation are
      helpful. Having these is nice for reverse-engineering,
      especially new pages. They do inject a lot of noise, though, and
      from there, being able to easily ignore these is nice.
     */
    function(request) {
        //chrome.extension.getBackgroundPage().console.log("Web request url:"+request.url);
        var formdata = {};
        let event;
        if(request.requestBody) {
            formdata = request.requestBody.formData;
        }
        if(!formdata) {
            formdata = {};
        }
        if(RAW_DEBUG) {
            lo_event.logEvent('raw_http_request', {
                'url':  request.url,
                'form_data': formdata
            });
        }

        if(this_a_google_docs_save(request)){
            //chrome.extension.getBackgroundPage().console.log("Google Docs bundles "+request.url);
            try {
                /* We should think through which time stamps we should log. These are all subtly
                  different: browser event versus request timestamp, as well as user time zone
                  versus GMT. */
                event = {
                    'doc_id':  googledocs_id_from_url(request.url),
                    'url': request.url,
                    'bundles': JSON.parse(formdata.bundles),
                    'rev': formdata.rev,
                    'timestamp': parseInt(request.timeStamp, 10)
                }
                logFromServiceWorker(event);
                lo_event.logEvent('google_docs_save', event);
            } catch(err) {
                /*
                  Oddball events, like text selections.
                */
                event = {
                    'doc_id':  googledocs_id_from_url(request.url),
                    'url': request.url,
                    'formdata': formdata,
                    'rev': formdata.rev,
                    'timestamp': parseInt(request.timeStamp, 10)
                }
                lo_event.logEvent('google_docs_save_extra', event);
            }
        } else if(this_a_google_docs_bind(request)) {
            logFromServiceWorker(request);
        } else {
            logFromServiceWorker("Not a save or bind: "+request.url);
        }
    },
    { urls: ["*://docs.google.com/*"] },
    ['requestBody']
)

// re-injected scripts when chrome extension is reloaded, upgraded or re-installed
// https://stackoverflow.com/questions/10994324/chrome-extension-content-script-re-injection-after-upgrade-or-install
chrome.runtime.onInstalled.addListener(reinjectContentScripts);
async function reinjectContentScripts() {
    for (const contentScript of chrome.runtime.getManifest().content_scripts) {
        for (const tab of await chrome.tabs.query({url: contentScript.matches})) {
            // re-inject content script
            await chrome.scripting.executeScript({
                target: {tabId: tab.id, allFrames: true},
                files: contentScript.js,
            }, function () {
                if (!chrome.runtime.lastError) {
                    console.log('Content script re-injected successfully');
                }
            });
        }
    }
}

// Let the server know we've loaded.
lo_event.logEvent("extension_loaded", {});

// Send the server the user info. This might not always be available.
profileInfoWrapper(function callback(userInfo) {
    lo_event.logEvent("chrome_identity", userInfo);
});

// And let the console know we've loaded
// chrome.extension.getBackgroundPage().console.log("Loaded"); remove
logFromServiceWorker("Loaded");
