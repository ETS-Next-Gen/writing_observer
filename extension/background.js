/*
Background script. This works across all of Google Chrome. 
*/

var WRITINGJS_SERVER = "https://test.mitros.org/webapi/";

function gmail_text() {
    /*
      This function returns all the editable text in the current gmail
      window. Note that in a threaded discussion, it's possible to
      have several open on the same page.

      This is brittle; Google may change implementation and this will
      break.
     */
    var documents = document.getElementsByClassName("editable");
    for(document in documents) {
	documents[document] = documents[document].innerHTML;
    }
    return documents;
}

function writingjs_ajax(data) {
    /*
      Helper function to send a logging AJAX request to the server.
      This function takes a JSON dictionary of data.

      TODO: Convert to a queue for offline operation using Chrome
      Storage API? Cache to Chrome Storage? Chrome Storage doesn't
      support meaningful concurrency,

      TODO: Abstract out into a common function,
     */
    httpRequest = new XMLHttpRequest();
    //httpRequest.withCredentials = true;
    httpRequest.open("POST", WRITINGJS_SERVER);
    httpRequest.send(JSON.stringify(data));
}

function writing_eventlistener(event) {
    /* 
       Here, we process keystroke events and send them to the server. We want fine-grained writing data
       with timing.
     */
    var event_data = {};
    event_data["event_type"] = "keypress";
    properties = ['altKey', 'charCode', 'code', 'ctrlKey', 'isComposing', 'key', 'keyCode', 'location', 'metaKey', 'repeat', 'shiftKey', 'which', 'isTrusted', 'timeStemp', 'type'];
    for (var property in properties) {
	event_data[properties[property]] = event[properties[property]];
    }
    event_data['date'] = new Date().toLocaleString('en-US');
    console.log(JSON.stringify(event_data));
    writingjs_ajax(event_data);
}

chrome.webRequest.onBeforeRequest.addListener(
    function(request) {
	var formdata = {};
	if(request.requestBody) {
	    formdata = request.requestBody.formData;
	}
	if(!formdata) {
	    formdata = {};
	}
	writingjs_ajax({
	    'event_type':'request',
	    'url': request.url,
	    'from_data': formdata
	});
    },
    { urls: ["*://docs.google.com/*"/*, "*://mail.google.com/*"*/] },
    ['requestBody']
)

/*chrome.tabs.executeScript({
    code: 'console.log("addd")'
});*/

writingjs_ajax({"Loaded now": true});
