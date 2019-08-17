var WRITINGJS_SERVER = "https://test.mitros.org/webapi/";

function writingjs_ajax(data) {
    httpRequest = new XMLHttpRequest();
    //httpRequest.withCredentials = true;
    httpRequest.open("POST", WRITINGJS_SERVER);
    httpRequest.send(JSON.stringify(data));
}

function writing_eventlistener(event) {
    var event_data = {};
    event_data["event_type"] = "keypress";
    properties = ['altKey', 'charCode', 'code', 'ctrlKey', 'isComposing', 'key', 'keyCode', 'location', 'metaKey', 'repeat', 'shiftKey', 'which', 'isTrusted', 'timeStemp', 'type'];
    for (var property in properties) {
	event_data[properties[property]] = event[properties[property]];
    }
    event_data['date'] = new Date().toLocaleString('en-US')
    console.log(JSON.stringify(event_data));
    writingjs_ajax(event_data);
}

chrome.webRequest.onBeforeRequest.addListener(
    function(request) {
	writingjs_ajax({
	    'event_type':'request',
	    'url': request.url,
	    'from_data': request.requestBody.formData
	});
    },
    { urls: ["*://docs.google.com/*"] },
    ['requestBody']
)

/*chrome.tabs.executeScript({
    code: 'console.log("addd")'
});*/

writingjs_ajax({"Loaded": true});
