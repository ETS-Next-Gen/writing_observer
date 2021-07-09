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
    console.trace(error_string);
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
    console.log(event);
    chrome.runtime.sendMessage(event);
}

//Data structure specifying the events we want to capture from the browser.
EVENT_LIST = {
    "keystroke": {
	"events": [
	    "keypress", "keydown", "keyup"
	],
	"properties": [
	    'altKey', 'charCode', 'code', 'ctrlKey', 'isComposing', 'key', 'keyCode',
	    'location', 'metaKey', 'repeat', 'shiftKey', 'which', 'isTrusted',
	    'timeStamp', 'type'],
	"target": "document"
    },
    "mouseclick": {
	"events": [
	    "mouseclick", "mousedown", "mouseup"
	],
	"properties": [
	    "button", "buttons",
	    "clientX", "clientY",
	    "layerX", "layerY",
	    "offsetX", "offsetY",
	    "screenX", "screenY",
	    "movementX", "movementY",
	    'altKey', 'ctrlKey',
	    'metaKey', 'shiftKey', 'which', 'isTrusted',
	    'timeStamp', 'type',
	    'target.id',
	    'target.innerText',
	    'target.localName'
	],
	"target": "document"
    },
    "attention": {
       "events": ["focusin", "focusout"],
	// Not all of these are required for all events...
	"properties": ['target', 'bubbles', 'cancelable', 'isTrusted', 'timeStamp', 'type'],
	"target": "window"
    },
    "visibility": {
        "events": ["visibilitychange"],
        "properties": ['target', 'bubbles', 'cancelable', 'isTrusted', 'timeStamp', 'type'],
        "target": "document"
    },
    "save": {
        "events": ["google_docs_save"],
        "properties": [
             "doc_id", "bundles", 
             "event", "timestamp"
        ],      
        "target": "window"
    },
    "load": {
        "events": ["document_loaded"],
        "properties": [
              "doc_id", "event",
              "history", "title",
              "timestamp"
        ],
        "target": "window"
    },
    "readystate": {
        "events": ["readystatechange"],
        "properties": [
              "doc_id", "event",
              "target", "timestamp", "type"
        ],
        "target": "window"
    },
    "pageshow": {
        "events": ["pageshow"],
        "properties": ['target', 'bubbles', 'cancelable', 'isTrusted', 'timeStamp', 'type'],
        "target": "window"
   }
};

function generic_eventlistener(event_type, frameindex, event) {
    /*
       This function captures any events specified in EVENT_LIST and passes them to the server.
    */
    return function(event) {
	/*
	  Listen for events, and pass them back to the background page.
	*/
	var event_data = {};
	event_data["event_type"] = event_type;
	properties = EVENT_LIST[event_type].properties;
	var keystroke_data = {};
	for (var property in properties) {
	    const prop = treeget(event, properties[property]);
	    if(prop !== null) {
		keystroke_data[properties[property]] = treeget(event, properties[property]);
	    }
	}
        if (frameindex===undefined) {
            frameindex='0';
        }
        console.log(frameindex, event);

        event_data[event_type] = keystroke_data;
        event_data['frameindex']=frameindex;
        log_event(event_type, event_data);
    }
}

// Set up to observe changes in the document, not just events.
var editor = document.querySelector('.kix-appview-editor');

//Data structure where we store information about which events to log how.
//The categories insert, delete, input, clear, replace are hard coded into the
//function that sets up the MutationObserver. Once we know that, we know
//what information in the context will tell us whether to log a change.
//We start by checking the target className, which is the second level key.
//For insert and delete events, we have to also check the classname of
//the node being inserted or deleted. Then we apply the label specified
//as the last item in each record.
var mutationsObserved = {
        "insert": {
            "docos-stream-view": ["docos-docoview-resolve-button-visible","add-comment"],
            "docos-docoview-replycontainer": ["docos-replyview-comment","add-reply"]
        },
        "delete": {
            "docos-docoview-rootreply": ["docos-replyview-comment","delete-comment"],        
            "docos-docoview-replycontainer": ["docos-replyview-comment","delete-reply"],                
        },
        "input": {
            "docos-input-textarea": [null, "type-input"]
        },
        "clear": {
            "docos-input-textarea": [null, "clear-input"]       
        },
        "replace": {
            "docos-replyview-body": [null, "edit-comment"]
        }       
    } 

function prepareMutationObserver(mutationsObserved) {
    /*
        Set up a MutationObserver that will use the mutationObserved dictionary
        to tell it which changes to log and what label to log it as.
    */
    var observer = new MutationObserver(function (mutations) {
           mutations.forEach(function (mutation) {
           //log_event("general",mutation)

           // We only want to detect page change events that are initiated by the user.
           // Changes that happen during loading are simply effects of the loading process.
           if (!loading) {
             if (mutation.addedNodes.length > 0 && mutation.removedNodes.length == 0) {
               var entry = {
                   mutation: mutation,
                   el: mutation.target,
                   type: "mutation",
                   numAdded: mutation.addedNodes.length,
                   numDel: mutation.removedNodes.length,
                   value: mutation.value,
                   attributeName: mutation.attributeName,
                   className: mutation.target.className,
                   firstRemovedClassName: ' ',
                   firstAddedClassName: mutation.addedNodes[0].className,
                   parentID:  ''
               }
               inserts = mutationsObserved["insert"];
               for (var targetClass in inserts) {
                      var addedClass = inserts[targetClass][0];
                      var label = inserts[targetClass][1];
                      if (entry.className.indexOf(targetClass)>=0 && entry.firstAddedClassName.indexOf(addedClass)>=0) {
                          entry.type = label;
                          log_event(mutation.type,entry);
                      }
               }
              }
              else if (mutation.addedNodes.length == 0 && mutation.removedNodes.length > 0) {
                if (mutation.removedNodes[0].nodeType == Node.TEXT_NODE) {
                    var entry = {
                        mutation: mutation,
                        el: mutation.target,
                        type: "mutation",
                        numAdded: mutation.addedNodes.length,
                        numDel: mutation.removedNodes.length,
                        value: mutation.target.value,
                        attributeName: mutation.attributeName,
                        className: mutation.target.className,
                        firstRemovedClassName: mutation.removedNodes[0].className,
                        firstAddedClassName: ' ',
                        parentID: mutation.target.parentNode.id
                     }
                     clears = mutationsObserved["clear"];
                     for (var targetClass in clears) {
                            var label = clears[targetClass][1];
                            if (entry.className.indexOf(targetClass)>=0) {
                                entry.type = label;
                                log_event(mutation.type,entry);
                             }
                     }
                  }
                  else {
                    var entry = {
                        mutation: mutation,
                        el: mutation.target,
                        type: "mutation",
                        numAdded: mutation.addedNodes.length,
                        numDel: mutation.removedNodes.length,
                        value: mutation.value,
                        attributeName: mutation.attributeName,
                        className: mutation.target.className,
                        firstRemovedClassName: mutation.removedNodes[0].className,
                        firstAddedClassName: ' ',
                        parentID: ''
                    }
                    deletes = mutationsObserved["delete"];
                    for (var targetClass in deletes) {
                           var addedClass = deletes[targetClass][0];
                           var label = deletes[targetClass][1];
                           if (entry.className.indexOf(targetClass)>=0 && entry.firstRemovedClassName.indexOf(addedClass)>=0) {
                               entry.type = label;
                               log_event(mutation.type,entry);
                            }
                    }
                }
               }
               else if (mutation.addedNodes.length > 0 && mutation.removedNodes.length > 0 &&
                  mutation.removedNodes[0].nodeType == Node.TEXT_NODE &&
                  mutation.addedNodes[0].nodeType == Node.TEXT_NODE
             ) {
                 var entry = {
                    mutation: mutation,
                    el: mutation.target,
                    type: "mutation",
                    numAdded: mutation.addedNodes.length,
                    numDel: mutation.removedNodes.length,
                    value: mutation.addedNodes[0].data,
                    attributeName: mutation.attributeName,
                    className: mutation.target.className,
                    firstRemovedClassName: ' ',
                    firstAddedClassName: ' ',
                    parentID: mutation.target.parentNode.id
                 }

                 replacements = mutationsObserved["replace"];
                 for (var targetClass in replacements) {
                        var label = replacements[targetClass][1];
                        if (entry.className.indexOf(targetClass)>=0) {
                            entry.type = label;
                            log_event(mutation.type,entry);
                         }
                 }
               }
               else if (mutation.type=='characterData') {
                var entry = {
                    mutation: mutation,
                    el: mutation.target,
                    type: "mutation",
                    numAdded: mutation.addedNodes.length,
                    numDel: mutation.removedNodes.length,
                    value: mutation.target.data,
                    attributeName: mutation.attributeName,
                    className: mutation.target.parentNode.className,
                    firstRemovedClassName: ' ',
                    firstAddedClassName: ' ',
                    parentID: mutation.target.parentNode.id
                }

                 inputs = mutationsObserved["input"];
                 for (var targetClass in inputs) {
                     var label = inputs[targetClass][1];
                     if (entry.className.indexOf(targetClass)>=0) {
                        entry.type = label;
                        log_event(mutation.type,entry);
                     }
                 }
             }
           }
        });
    });
    return observer;
}

var options = {
    attributes: false,
    childList: true,
    characterData: true,
    subtree: true  
};

//OK, now create the MutationObserver and start running it on the document.
observer = prepareMutationObserver(mutationsObserved)
observer.observe(editor, options);

//Now initialize the event listeners.

//We want to listen to events in all iFrames, as well as the main content document.
var frames = Array.from(document.getElementsByTagName("iframe"));

// We should really make a list of documents instead of a fake iframe....
frames.push({'contentDocument': document})

var s = document.createElement('script');
s.src = chrome.runtime.getURL('pageinfo.js');

//Add an event listener to each iframe in the iframes under frames.
for(var event_type in EVENT_LIST) {

    for(var event_idx in EVENT_LIST[event_type]['events']) {
	js_event = EVENT_LIST[event_type]['events'][event_idx];
	target = EVENT_LIST[event_type]['target']
	if(target === 'document') {
 
	    for(var iframe in frames){
		if(frames[iframe].contentDocument) {
                    console.log(iframe)
                    frames[iframe].contentDocument.addEventListener(js_event, generic_eventlistener(event_type,iframe));
              }               
	    }
	} else if (target === 'window') {
            window.addEventListener(js_event, generic_eventlistener(event_type));
	}
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

//When the script is loaded, we assume the page is still being loaded
var loading = 1;

function writing_onload() {
    if(this_is_a_google_doc()) {
	log_event("document_loaded", {
	    "partial_text": google_docs_partial_text()
	})
	google_docs_version_history();
    }
    // So once we hit a load event, we can assume we're not loading any more.
    loading = 0;
}

window.addEventListener("load", writing_onload); 
