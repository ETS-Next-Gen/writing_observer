/*
Background script. This works across all of Google Chrome. 
*/

var WRITINGJS_AJAX_SERVER = null;

var webSocket = null;
var EXPERIMENTAL_WEBSOCKET = false;


var event_queue = [];


/*
  FSM

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

function dequeue_events() {
    // If we have not yet initialized, we rely on the queue to be
    // flushed once we are initialized.
    if(!WRITINGJS_AJAX_SERVER) {
	return
    }
    while(event_queue.length > 0) {
	writingjs_ajax(event_queue.shift());
    }
    /*
	if(EXPERIMENTAL_WEBSOCKET) {
	if((webSocket == null) || (webSocket.readyState != 1) ) {
	    window.setTimeout(reset_websocket, 1000);
	    return;
	}
	var event = event_queue.shift();
	webSocket.send(JSON.stringify(event));
    }*/
}


function writingjs_ajax(data) {
    /*
      Helper function to send a logging AJAX request to the server.
      This function takes a JSON dictionary of data.

      TODO: Convert to a queue for offline operation using Chrome
      Storage API? Cache to Chrome Storage? Chrome Storage doesn't
      support meaningful concurrency,
     */

    httpRequest = new XMLHttpRequest();
    //httpRequest.withCredentials = true;
    httpRequest.open("POST", WRITINGJS_AJAX_SERVER);
    httpRequest.send(JSON.stringify(data));
}

function enqueue_event(event_type, event) {
    // TODO: Add username
    event['source'] = 'org.mitros.writing-analytics';
    event['version'] = 'alpha';
    event['ts'] = Date.now();
    event['human_ts'] = Date();
    event['iso_ts'] = new Date().toISOString;
    event['event'] = event_type;
    if(event['wa-source'] = null) {
	event['wa-source'] = 'background-page';
    }

    event_queue.push(event);

    dequeue_events();
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
    chrome.identity.getProfileInfo(function(userInfo) {
	enqueue_event("chrome_identity", {"email": userInfo.email,
					  "id": userInfo.id
					 });
    });
}

function reset_websocket() {
    if((webSocket == null) || (webSocket.readyState != 1) ) {
	webSocket = new WebSocket("wss://writing.hopto.org/wsapi/");
	webSocket.onopen = dequeue_events;
    }
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

var RAW_DEBUG = false; // Do not save debug requests. We flip this frequently. Perhaps this should be a cookie or browser.storage? 

// Figure out the system settings. Note this is asynchronous, so we
// chain dequeue_events when this is done.
chrome.storage.sync.get(['process-server'], function(result) {
    //WRITINGJS_AJAX_SERVER = result['process-server'];
    if(!WRITINGJS_AJAX_SERVER) {
	WRITINGJS_AJAX_SERVER = "https://writing.hopto.org/webapi/";
    }
    dequeue_events();
});

// Listen for the keystroke messages from the page script and forward to the server.
chrome.runtime.onMessage.addListener(
    function(request, sender, sendResponse) {
	chrome.extension.getBackgroundPage().console.log("Got message");
	chrome.extension.getBackgroundPage().console.log(request);
	console.log(sender);
	request['wa-source'] = 'client-page';
	enqueue_event(request['event'], request);
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
	chrome.extension.getBackgroundPage().console.log("Web request url:"+request.url);
	var formdata = {};
	if(request.requestBody) {
	    formdata = request.requestBody.formData;
	}
	if(!formdata) {
	    formdata = {};
	}
	if(RAW_DEBUG) {
	    enqueue_event('raw_http_request', {
		'url':  request.url,
		'form_data': formdata
	    });
	}

	if(this_a_google_docs_save(request)){
	    chrome.extension.getBackgroundPage().console.log("Google Docs bundles "+request.url);
	    console.log(formdata.bundles);
	    event = {
		'doc_id':  googledocs_id_from_url(request.url),
		'bundles': JSON.parse(formdata.bundles),
		'rev': formdata.rev,
		'timestamp': parseInt(request.timeStamp, 10)
	    };
	    chrome.extension.getBackgroundPage().console.log(event);
	    enqueue_event('google_docs_save', event);
	} else {
	    chrome.extension.getBackgroundPage().console.log("Not a save: "+request.url);
	}
    },
    { urls: ["*://docs.google.com/*"/*, "*://mail.google.com/*"*/] },
    ['requestBody']
)

// Let the server know we've loaded.
enqueue_event("extension_loaded", {});

// Send the server the user info. This might not always be available.
chrome.identity.getProfileUserInfo(function callback(userInfo) {
    enqueue_event("google-chrome-identity", userInfo);
});

// And let the console know we've loaded
chrome.extension.getBackgroundPage().console.log("Loaded");
