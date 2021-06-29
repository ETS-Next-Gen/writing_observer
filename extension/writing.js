/* 
   Page script. This is injected into each web page on associated web sites.
*/ 

/* For debugging purposes: we know the extension is active */
document.body.style.border = "5px solid blue";

function log_error(error_string) {
    /* 
       We should send errors to the server, but for now, we
       log to the console.
     */ 
    console.log(error_string);
}

function doc_id() {
    /*
      Extract the Google document ID from the window
    */
    try {
	return googledocs_id_from_url(window.location.href);
    } catch(error) {
	log_error("Couldn't read document id");
	return null;
    }
}

function this_is_a_google_doc() {
    /*
      Returns 'true' if we are in a Google Doc
    */
    return window.location.href.search("://docs.google.com/") != -1;
}

function log_event(event_type, event) {
    /*
      We pass an event, annotated with the page document ID and title,
      to the background script
    */
    event["title"] = google_docs_title();
    event["doc_id"] = doc_id();
    event['event'] = event_type;

    chrome.runtime.sendMessage(event);
}

function writing_eventlistener(event) {
    /*
      Listen for keystroke events, and pass them back to the background page.
     */
    var event_data = {};
    event_data["event_type"] = "keypress";
    properties = [
	'altKey', 'charCode', 'code', 'ctrlKey', 'isComposing', 'key', 'keyCode',
	'location', 'metaKey', 'repeat', 'shiftKey', 'which', 'isTrusted',
	'timeStamp', 'type'];
    var keystroke_data = {};
    for (var property in properties) {
	keystroke_data[properties[property]] = event[properties[property]];
    }
    event_data['keystroke'] = keystroke_data;
    log_event("keystroke", event_data);
}



document.addEventListener("keypress", writing_eventlistener);
document.addEventListener("keydown", writing_eventlistener);
document.addEventListener("keyup", writing_eventlistener);

var iframes = document.getElementsByTagName("iframe")
for(iframe in iframes){
    if(iframes[iframe].contentDocument) {
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

      We will probably disable gmail analytics in the pilot.
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
      Return the title of a Google Docs document.

      Note this is not guaranteed 100% reliable since Google
      may change the page structure.
    */
    try {
	return document.getElementsByClassName("docs-title-input")[0].value;
    } catch(error) {
	log_error("Couldn't read document title");
	return null;
    }
}

function google_docs_partial_text() {
    /*
      Return the *loaded* text of a Google Doc. Note that for long
      documents, this may not be the *complete* text since off-screen
      pages may be lazy-loaded. The text omits formatting, which is
      helpful for many types of analysis

      We want this for redundancy: we'd like to confirm we're correctly
      reconstructing text.
     */
    try {
	return document.getElementsByClassName("kix-page")[0].innerText;
    } catch(error) {
	log_error("Could get document text");
	return null;
    }
}

function google_docs_partial_html() {
    /*
      Return the *loaded* HTML of a Google Doc. Note that for long
      documents, this may not be the *complete* HTML, since off-screen
      pages may be lazy-loaded. This includes HTML formatting, which
      may be helpful, but is incredibly messy.
      
      I hate Google's HTML. What's wrong with simple, clean, semantic
      <b> tags and classes? Why do we need something like this instead:

      <span class="kix-wordhtmlgenerator-word-node" style="font-size:14.666666666666666px;font-family:Arial;color:#000000;background-color:transparent;font-weight:700;font-style:normal;font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;">

      Seriously, Google?

      And yes, if you download documents from Google, it's a mess like
      this too.
     */
    return document.getElementsByClassName("kix-page")[0].innerHTML;
}

function executeOnPageSpace(code){
    /* This is from 
       https://stackoverflow.com/questions/9602022/chrome-extension-retrieving-global-variable-from-webpage

       It is used to run code outside of the extension isolation box,
       for example to access page JavaScript variables.
     */
    // create a script tag
    var script = document.createElement('script')
    script.id = 'tmpScript'
    // place the code inside the script. later replace it with execution result.
    script.textContent = 
	'document.getElementById("tmpScript").textContent = JSON.stringify(' + code + ')'
    // attach the script to page
    document.documentElement.appendChild(script)
    // collect execution results
    let result = document.getElementById("tmpScript").textContent
    // remove script from page
    script.remove()
    return JSON.parse(result)
}

function google_docs_version_history() {
    /*
      Grab the _complete_ version history of a Google Doc. We do this
      on page load. Note that this may lead to a lot of data. But this
      lets us do most of our analytics on documents created or edited
      without our extension.

      Note that if Google changes their implementation, this may
      break. We don't want to promise to users this will always
      work. But it's good to have for the pilot.

      It also lets us debug the system.
     */
    var token = executeOnPageSpace("_docs_flag_initialData.info_params.token");

    metainfo_url = "https://docs.google.com/document/d/"+doc_id()+"/revisions/tiles?id="+doc_id()+"&start=1&showDetailedRevisions=false&filterNamed=false&token="+token+"&includes_info_params=true"

    fetch(metainfo_url).then(function(response) {
	response.text().then(function(text) {
	    tiles = JSON.parse(text.substring(5)); // Google adds a header to prevent JavaScript injection. This removes it.
	    var first_revision = tiles.firstRev;
	    var last_revision = tiles.tileInfo[tiles.tileInfo.length - 1].end;
	    version_history_url = "https://docs.google.com/document/d/"+doc_id()+"/revisions/load?id="+doc_id()+"&start="+first_revision+"&end="+last_revision;
	    fetch(version_history_url).then(function(history_response) {
		history_response.text().then(function(history_text) {
		    log_event(
			"document_history",
			{'history': JSON.parse(history_text.substring(4))}
		    );
		});
	    });
	});
    });
}

function writing_onload() {
    if(this_is_a_google_doc()) {
	log_event("document_loaded", {
	    "partial_text": google_docs_partial_text()
	})
	google_docs_version_history();
    }
}

window.addEventListener("load", writing_onload);
