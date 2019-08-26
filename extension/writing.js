/* 
Page script. This is injected into each web page on associated web sites.
*/ 

document.body.style.border = "5px solid blue";

function doc_id() {
    return googledocs_id_from_url(window.location.href);
}

function writing_eventlistener(event) {
    var event_data = {};
    event_data["event_type"] = "keypress";
    properties = ['altKey', 'charCode', 'code', 'ctrlKey', 'isComposing', 'key', 'keyCode', 'location', 'metaKey', 'repeat', 'shiftKey', 'which', 'isTrusted', 'timeStemp', 'type'];
    for (var property in properties) {
	event_data[properties[property]] = event[properties[property]];
    }
    event_data['date'] = new Date().toLocaleString('en-US');
    event_data['id'] = doc_id();
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
	iframes[iframe].contentDocument.addEventListener("keydown", writing_eventlistener);
	iframes[iframe].contentDocument.addEventListener("keyup", writing_eventlistener);
    }
}


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
	documents[document] = {
	    'text': documents[document].innerHTML
	};
    }
    return documents;
}

function google_docs_title() {
    /*
      Return the title of a Google Docs document
     */
    return document.getElementsByClassName("docs-title-input")[0].value;
}

function google_docs_partial_text() {
    /*
      Return the *loaded* text of a Google Doc. Note that for long
      documents, this may not be the *complete* text since off-screen
      pages may be lazy-loaded. The text omits formatting, which is
      helpful for many types of analysis
     */
    return document.getElementsByClassName("kix-page")[0].innerText;
}

function google_docs_partial_html() {
    /*
      Return the *loaded* HTML of a Google Doc. Note that for long
      documents, this may not be the *complete* HTML, since off-screen
      pages may be lazy-loaded. This includes HTML formatting, which
      may be helpful, but is incredibly messy.
      
      I hate Google's HTML. What's wrong with simple, clean, semantic
      <b> tags? Why do we need something like this instead:
      <span class="kix-wordhtmlgenerator-word-node" style="font-size:14.666666666666666px;font-family:Arial;color:#000000;background-color:transparent;font-weight:700;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;">
      Seriously, Google? 
     */
    return document.getElementsByClassName("kix-page")[0].innerHTML;
}

writingjs_ajax({
    "event_type": "Google Docs loaded",
    "partial_text": google_docs_partial_text(),
//    "partial_html": google_docs_partial_html(),
    "title": google_docs_title(),
    "id": doc_id
})
