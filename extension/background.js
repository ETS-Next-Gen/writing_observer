/*
Background script. This works across all of Google Chrome. 
*/

function this_a_google_docs_save(request) {
    /* 
       Check if this is a Google Docs save request. Return true for something like:
       https://docs.google.com/document/d/1lt_lSfEM9jd7Ga6uzENS_s8ZajcxpE0cKuzXbDoBoyU/save?id=dfhjklhsjklsdhjklsdhjksdhkjlsdhkjsdhsdkjlhsd&sid=dhsjklhsdjkhsdas&vc=2&c=2&w=2&smv=2&token=lasjklhasjkhsajkhsajkhasjkashjkasaajhsjkashsajksas&includes_info_params=true
       And false otherwise
    */
    if(request.url.match(/.*:\/\/docs\.google\.com\/document\/d\/([^\/]*)\/save/i)) {
	return true;
    }
    return false;
}

var RAW_DEBUG = false; // Do not save debug requests. We flip this frequently. Perhaps this should be a cookie or browser.storage? 

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
	chrome.extension.getBackgroundPage().console.log("Web request");
	var formdata = {};
	if(request.requestBody) {
	    formdata = request.requestBody.formData;
	}
	if(!formdata) {
	    formdata = {};
	}
	if(RAW_DEBUG) {
	    writingjs_ajax({
		'event_type': 'raw_request',
		'url':  request.url,
		'form_data': formdata
	    });
	}
	if(this_a_google_docs_save(request)){
	    event = {
		'event_type': 'google_docs_save',
		'doc_id':  googledocs_id_from_url(request.url),
		'bundles': JSON.parse(formdata.bundles),
		'rev': formdata.rev,
		'timestamp': parseInt(request.timeStamp, 10)
	    };
	    chrome.extension.getBackgroundPage().console.log("Google Docs keypress");
	    chrome.extension.getBackgroundPage().console.log(event);
	    writingjs_ajax(event);
	} else {
	    chrome.extension.getBackgroundPage().console.log("Not a save");
	}
	
    },
    { urls: ["*://docs.google.com/*"/*, "*://mail.google.com/*"*/] },
    ['requestBody']
)

chrome.runtime.onMessage.addListener(
    function(request, sender, sendResponse) {
	chrome.extension.getBackgroundPage().console.log("Got message");
	chrome.extension.getBackgroundPage().console.log(request);
	writingjs_ajax(request);
    }
);


/*chrome.tabs.executeScript({
    code: 'console.log("addd")'
});*/

writingjs_ajax({"Loaded now": true});

chrome.identity.getProfileUserInfo(function callback(userInfo) {
    writingjs_ajax(userInfo);
});

chrome.extension.getBackgroundPage().console.log("Loaded");
