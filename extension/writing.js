/* 
Page script. This is injected into each web page on associated web sites.
*/ 

var WRITINGJS_SERVER = "https://test.mitros.org/webapi/";

function writingjs_ajax(data) {
    httpRequest = new XMLHttpRequest();
    //httpRequest.withCredentials = true;
    httpRequest.open("POST", WRITINGJS_SERVER);
    httpRequest.send(JSON.stringify(data));
}

document.body.style.border = "5px solid blue";

function writing_eventlistener(event) {
    var event_data = {};
    event_data["event_type"] = "keypress";
    properties = ['altKey', 'charCode', 'code', 'ctrlKey', 'isComposing', 'key', 'keyCode', 'location', 'metaKey', 'repeat', 'shiftKey', 'which', 'isTrusted', 'timeStemp', 'type'];
    for (var property in properties) {
	event_data[properties[property]] = event[properties[property]];
    }
    event_data['date'] = new Date().toLocaleString('en-US');
    event_data['url'] = window.location.href;
    console.log(event_data['url']);

    console.log(JSON.stringify(event_data));
    writingjs_ajax(event_data);
}

document.addEventListener("keypress", writing_eventlistener);
document.addEventListener("keydown", writing_eventlistener);
document.addEventListener("keyup", writing_eventlistener);

var iframes = document.getElementsByTagName("iframe")
for(iframe in iframes){
    if(iframes[iframe].contentDocument) {
	console.log(iframes[iframe].contentDocument);
	iframes[iframe].contentDocument.addEventListener("keypress", writing_eventlistener);
    }
}
/*chrome.webRequest.onBeforeRequest.addListener(
    function(request) {
	if (request.url.indexOf('/save?') != -1) {
	    // Regexp and general theme of code based on
	    // http://features.jsomers.net/how-i-reverse-engineered-google-docs/
	    var docId = request.url.match("docs\.google\.com\/document\/d\/(.*?)\/save")[1]

	    var data = {
		"bundles": request.body.formData.bundles,
		"revNo": request.body.formData.rev,
		"docId": docId,
		"timeStamp" : request.timeStamp
	    }

	    writingjs_ajax(data);
	    //draftback.addPendingRevision(data, request.requestId)
	}
    },
    { urls: ["*://docs.google.com/*"] },
    ['requestBody']
)
*/
