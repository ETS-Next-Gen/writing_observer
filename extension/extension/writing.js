/*
   Page script. This is injected into each web page on associated web sites.
*/

/* For debugging purposes: we know the extension is active */
document.body.style.border = "5px solid blue";

/*
   General Utility Functions
*/

function log_error(error_string) {
    /*
       We should send errors to the server, but for now, we
       log to the console.
    */
    console.trace(error_string);
}

function log_event(event_type, event) {
    /*
      We pass an event, annotated with the page document ID and title,
      to the background script
    */
    // This is a compromise. We'd like to be similar to xAPI / Caliper, both
    // of which use the 'object' field with a bunch of verbose stuff.
    //
    // Verbosity is bad for analytics, but compatibility is good.
    //
    // This is how Caliper thinks of this: https://www.imsglobal.org/spec/caliper/v1p2#entity
    // This is how Tincan/xAPI thinks of this: https://xapi.com/statements-101/
    //
    // "Object" is a really bad name. Come on. Seriously?
    event["object"] = {
        "type": "http://schema.learning-observer.org/writing-observer/",
        "title": google_docs_title(),
        "id": doc_id(),
        "url": window.location.href,
    }

    event['event'] = event_type;
    // We want to track the page status during events. For example,
    // Google Docs inserts comments during the document load.
    event['readyState'] = document.readyState;

    // uncomment to watch events being logged from the client side with devtools
    // console.log(event);

    if (chrome.runtime.id !== undefined) {
        chrome.runtime.sendMessage(event);
    }
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
        return document.getElementsByClassName("kix")[0].innerText;
    } catch(error) {
        log_error("Could not get document text");
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

      <span class="kix-wordhtmlgenerator-word-node"
      style="font-size:14.666666666666666px;font-family:Arial;color:#000000;
      background-color:transparent;font-weight:700;font-style:normal;
      font-variant:normal;text-decoration:none;vertical-align:baseline;white-space:pre;">

      Seriously, Google?

      And yes, if you download documents from Google, it's a mess like
      this too.
     */
    return document.getElementsByClassName("kix-page")[0].innerHTML;
}

function is_string(myVar) {
    /*
      Utility function to check whether a variable is a string.
      We need that because some Google docs graphical object classes
      are not strings.
    */
    if (typeof myVar === 'string' || myVar instanceof String) {
        return true;
    } else {
        return false;
    }
}

function injectScript(file_path, tag) {
    /* 
        This function is to inject a script from 'file_path' 
        into a specific DOM tag passed in as 'tag'
    */
    var node = document.getElementsByTagName(tag)[0];
    var script = document.createElement('script');
    script.setAttribute('type', 'text/javascript');
    script.setAttribute('src', file_path);
    node.appendChild(script);
}

function execute_on_page_space(code){
    /* This is from
       https://stackoverflow.com/questions/9602022/chrome-extension-retrieving-global-variable-from-webpage

       It is used to run code outside of the extension isolation box,
       for example to access page JavaScript variables.
     */

    if (!document.getElementById('tmpScript')) {
        injectScript(chrome.runtime.getURL('inject.js'), 'body');
    }
}

function google_docs_version_history(token) {
    /*
      Grab the _complete_ version history of a Google Doc. We do this
      on page load. Note that this may lead to a lot of data. But this
      lets us do most of our analytics on documents created or edited
      without our extension.

      Note that if Google changes their implementation, this may
      break. We don't want to promise to users this will always
      work. But it's good to have for the pilot.

      It also lets us debug the system.

      NOTE (CL) in past cases use of the execute on page space by itself triggered
      an error.  If it creates excessive delays or error due to history use the
      following code block in lieu of the next call. 

      try {
        var token = executeOnPageSpace("_docs_flag_initialData.info_params.token");
      } catch (error) {
     	log_event("Error on Page History.", {"ERROR" : error})
 	return -1;
      }
    */

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

/*
   Event Logging Code Block
*/

// Data structure specifying the events we want to capture from the browser.
// For keystroke and mouseclick events, we capture target and parent target info
// because it gives us info about what exactly got clicked on/changed.

EVENT_LIST = {
    "keystroke": {
        "events": [
            "keypress", "keydown", "keyup"
        ],
        "properties": [
            'altKey', 'buttons',
            'charCode', 'code',
            'ctrlKey', 'isComposing',
            'isTrusted', 'key',
            'keyCode', 'location',
            'metaKey', 'repeat',
            'shiftKey', 'target.className',
            'target.id', 'target.nodeType',
            'target.localName', 'timeStamp',
            'type', 'which'
        ],
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
            'metaKey', 'shiftKey',
            'which', 'isTrusted',
            'timeStamp', 'type',
            'target.id', 'target.className',
            'target.innerText', 'target.nodeType','target.localName',
            'target.parentNode.id', 'target.parentNode.className',
            'target.parentNode.nodeType', 'target.parentNode.localName'
        ],
        "target": "document"
    },
    "attention": {
       "events": ["focusin", "focusout"],
        // Not all of these are required for all events...
        "properties": [
            'bubbles', 'cancelable',
            'isTrusted', 'timeStamp',
            'relatedTarget.className', 'relatedTarget.id',
            'target.className', 'target.id',
            'target.innertext', 'target.nodeType',
            'target.localName', 'target.parentNode.className',
            'target.parentNode.id', 'target.parentNode.innerText',
            'target.parentNode.nodeType', 'target.parentNode.localName',
            'type',
        ],
        "target": "window"
    },
    "visibility": {
        "events": ["visibilitychange"],
        "properties": [
            'target', 'bubbles',
            'cancelable', 'isTrusted',
            'timeStamp', 'type'
        ],
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
};

// By having these, we have references to allow us to remove listeners later
// See refresh_stream_view_listeners
for(var event_type in EVENT_LIST) {
    EVENT_LIST[event_type]['listener'] = generic_eventlistener(event_type, -1);
}

function generic_eventlistener(event_type, frameindex) {
    /*
       This function calls eventlistener_prototype on setup, then
       calls the `refresh_stream_view_listeners` function, which dynamically
       adds listeners after focus events to handle events for dynamically
       created nodes in `docos-stream-view`.
    */

    return function(event) {
        /*
          Listen for events, and pass them back to the background page.
        */
        var event_data = {};
        event_data["event_type"] = event_type;
        properties = EVENT_LIST[event_type].properties;
        var property_data = {};
        for (var property in properties) {
            const prop = treeget(event, properties[property]);
            if(prop !== null) {
                property_data[properties[property]] = treeget(event, properties[property]);
            }
        }
        event_data[event_type] = property_data;
        event_data['frameindex'] = frameindex;
        log_event(event_type, event_data);

        // Dynamic updates of `docos-stream-view` means our initial set
        // of listeners doesn't always catch events that happen in the
        // comments div. Specifically, if the user clicks on the
        // 'Comments' button, or if they click on certain fields in
        // displayed comments, events don't get registered without the
        // extra step called by `refresh_stream_view_listeners()`.

        // TODO: figure out way to limit the number of times
        // `refresh_stream_view_listeners()` is called.

        // We don't really want to call it every time focus shifts,
        // but I'm not sure what specifically to listen for to
        // minimize the number of times we swap out event listeners on
        // the `docos-stream-view` element.
        if (event_type=='attention') {
            refresh_stream_view_listeners();
        }
    }
}

function refresh_stream_view_listeners() {
    /*
      This function supports dynamic refreshing of the listeners
      associated with docos-stream-view, which is the div in which
      comments are placed.
    */
    // Grab the comments div
    el = document.getElementById('docos-stream-view');
    if (!el) {
        return;
    }

    // Refresh mouseclick events
    for(var eventNo in EVENT_LIST["mouseclick"].events) {
        event = EVENT_LIST["mouseclick"].events[eventNo];
        el.removeEventListener(event, EVENT_LIST["mouseclick"]["listener"]);
        el.addEventListener(event, EVENT_LIST["mouseclick"]["listener"]);
    }

    // Refresh keystroke events
    for(var eventNo in EVENT_LIST["keystroke"].events) {
        event = EVENT_LIST["keystroke"].events[eventNo];
        el.removeEventListener(event, EVENT_LIST["keystroke"]["listener"]);
        el.addEventListener(event, EVENT_LIST["keystroke"]["listener"], true);
    }
}

var editor = document.querySelector('.kix-appview-editor');

// Function definitions completed.
// Now we initialize the generic event listener.

//We will listen to events in all iFrames, as well as the main content document.
var frames = Array.from(document.getElementsByTagName("iframe"));

// TODO: We should really make a list of documents instead of a fake iframe....
frames.push({'contentDocument': document})

// Add an event listener to each iframe in the iframes under frames.
for(var event_type in EVENT_LIST) {
    for(var event_idx in EVENT_LIST[event_type]['events']) {
        js_event = EVENT_LIST[event_type]['events'][event_idx];
        target = EVENT_LIST[event_type]['target']
        if(target === 'document') {
            for(var iframe in frames) {
                if(frames[iframe].contentDocument) {
                    frames[iframe].contentDocument.addEventListener(js_event, generic_eventlistener(event_type, iframe));
                }
            }
        } else if (target === 'window') {
            window.addEventListener(js_event, generic_eventlistener(event_type, iframe));
        }
    }
}

////////////////////////////////////
// MUTATION OBSERVER CODE BLOCK ////
////////////////////////////////////

// NOTE: The following code is designed to observe changes in the document,
// not just html events. (Right now we're not observing CSS changes
// such as setting an element to display: none. Some of those may be
// worth watching for Google Docs; for instance, when a comment is
// "resolved", it is merely hidden.)

// MUTATIONS_OBSERVED is the data structure where we store information
// about which html change events to log how. This functions as a rule
// base that governs what changes in the html document are logged and
// sent back to the server. This code is based on the  MutationObserver
// and mutationRecord classes. See:
//
// https://developer.mozilla.org/en-US/docs/Web/API/MutationObserver
// https://developer.mozilla.org/en-US/docs/Web/API/MutationRecord
//
// The format works like this:
//  "insert": {
//    ^^^
//  Category.
//  A term we
//  made up.
//  It describes
// the type of
//  change made
//  by the
//  mutationRecord.
//
//
// [ { “target”: "bif",  “added”: "bar",  “label”:"foo",   “watch”: "hoo"] , ... ]
//                       (or "removed")
//        ^^^              ^^^               ^^^                ^^^
//  Class of the         Class of the     Type label we     Class of the parent
//  target node where    node added       made up that      node whose inner
//  the change took      or removed       is sent to the    text we want to
//  place.                                Writing Observer  monitor. The innerText
//                                        server.           will be sent to the
//  }                                                       WO server.
var MUTATIONS_OBSERVED = {
    "insert": [
        {
            "target": "docos-stream-view",
            "added": "docos-docoview-resolve-button-visible",
            "label": "add-comment",
            "watch": "kix-discussion-plugin"
        },
        {
            "target": "docos-anchoreddocoview-content",
            "added": "docos-replyview-comment",
            "label": "add-reply",
            "watch": "kix-discussion-plugin"
        }
    ],
    "addtext": [
        {
            "target": "kix-spell-bubble-suggestion-text",
            "label": "view_spelling_suggestion",
            "watch": ""
        },
    ],
    "delete": [
        {
            "target": "docos-docoview-rootreply",
            "removed": "docos-replyview-suggest",
            "label": "resolve-suggestion",
            "watch": "kix-discussion-plugin"
        },
        {
            "target": "docos-docoview-rootreply",
            "removed": "docos-replyview-first",
            "label": "delete-comment",
            "watch": "kix-discussion-plugin"
        },
        {
            "target": "docos-docoview-replycontainer",
            "removed": "docos-replyview-comment",
            "label": "delete-reply",
            "watch": "kix-discussion-plugin"
        }
    ],
    "input": [
        {
            "target": "docos-input-textarea",
            "label": "type-input",
        }
    ],
    "clear": [
        {
            "target": "docos-input-textarea",
            "label": "clear-input",
        }
    ],
    "replace": [
        {
            "target": "docos-replyview-static",
            "label": "edit-comment",
            "watch": "kix-discussion-plugin"
        },
        {
            "target": "kix-spell-bubble-suggestion-text",
            "label": "view-suggestion-text",
        },
        {
            "target": "kix-spell-bubble",
            "label": "view_spelling_suggestion",
            "watch": ""
        },
    ],
    "suggest": [
        {
            "target": "docos-replyview-static",
            "label": "add-suggestion",
            "watch": "kix-discussion-plugin"
        }
    ],
    "other": [
    ]
}

function classify_mutation(mutation) {
    /*
      Determine what kind of change is being made: `insert`, `addtext`,
      `delete`, `replace`, `input`, `suggest`, or `other`.

      We will use the category label returned by this function as the
      key to the mutationObserved variable to get a list of relevant
      rules to apply.
    */
    if (mutation.addedNodes.length > 0 && mutation.removedNodes.length == 0) {
        if (mutation.addedNodes[0].nodeType == Node.TEXT_NODE) {
          return "addtext";
        } else {
          return "insert";
        }
    }
    else if (mutation.addedNodes.length == 0 && mutation.removedNodes.length > 0) {
        if (mutation.removedNodes[0].nodeType == Node.TEXT_NODE) {
            return "clear";
        }
        else {
            return "delete";
        }
    }
    else if (mutation.addedNodes.length > 0 && mutation.removedNodes.length > 0 &&
             mutation.removedNodes[0].nodeType == Node.TEXT_NODE &&
             mutation.addedNodes[0].nodeType == Node.TEXT_NODE
            ) {
        return "replace";
    }
    else if (mutation.type=='characterData') {
        return "input";
    }
    else if (mutation.addedNodes.length > 0 && mutation.removedNodes.length > 0 ) {
        return "suggest";
    }
    else {
        return "other";
    }
}

function find_ancestor (el, cls) {
    /*
       Utility function to find an ancestor node of a specified class.
    */
    while ((el = el.parentNode) && el.className.indexOf(cls) < 0) {}
    return el;
}

function fire_rule(mutation, event, actions, rule) {
    /*
      Common script to run when a mutationObserver rule has been matched.
    */

    event['event_type'] = actions[rule]['label'];

    // If we specify a window we want to watch, get the innerText
    if ('watched' in actions[rule]
        && find_ancestor(mutation.target,actions[rule]['watched'])) {
        event['context_content'] =
            find_ancestor(mutation.target,actions[rule]['watched']).innerText;
    }

    // Then send the logged event to the WO server.
    log_event(mutation.type,event);
}

function prepare_mutation_observer() {
    /*
      Set up a MutationObserver that will use the mutationObserved dictionary
      to tell it which changes to log and what label to log it as.
    */
    var observer = new MutationObserver(function (mutations) {
        mutations.forEach(function (mutation) {
            event = {}

            // This list guarantees that we'll have the information we need
            // to understand what happened in a change event.
            properties = [
                'addedNodes.length', 'addedNodes[0].className',
                'addedNodes[0].data', 'addedNodes[0].id',
                'addedNodes[0].innerText', 'addedNodes[0].nodeType',
                'removedNodes.length', 'removedNodes[0].className',
                'removedNodes[0].data', 'removedNodes[0].id',
                'removedNodes[0].innerText', 'removedNodes[0].nodeType',
                'target.className', 'target.data',
                'target.innerText', 'target.parentNode.id',
                'target.parentNode.className','type'
            ];

            // Populate the mutation_data subdictionary that we use to
            // pass the details of the mutation back to the WO sever.
            var mutation_data = {};
            for (var property in properties) {
                const prop = treeget(mutation, properties[property]);
                if (prop !== null) {
                    mutation_data[properties[property]] =
                        treeget(mutation, properties[property]);
                }
            }
            event['change'] = mutation_data;

            // uncomment this to observe all mutations in the console log.
            // console.log(mutation);

            // Now we apply the rules defined by MUTATIONS_OBSERVED to record
            // watched events.

            // First, check what kind of event this is
            category = classify_mutation(mutation);

            // Then record that category as event_type
            event['event_type']=category;

            // Filter the templates to those that are relevant to this category
            actions = MUTATIONS_OBSERVED[category];

            // Then loop through the available templates
            for (var rule in actions) {
                if (category=='insert'
                  && is_string(event.change['addedNodes[0].className'])
                    && event.change['addedNodes[0].className'].indexOf(actions[rule]['added'])>=0
                    && event.change['target.className'].indexOf(actions[rule]['target'])>=0
                   ) {
                    fire_rule(mutation, event, actions, rule);
                    break;
                }
                else if (category=='delete'
                         && is_string(event.change['removedNodes[0].className'])
                         && event.change['removedNodes[0].className'].indexOf(actions[rule]['removed'])>=0
                         && event.change['target.className'].indexOf(actions[rule]['target'])>=0
                        ) {
                    fire_rule(mutation, event, actions, rule);
                    break;
                }
                else if (category=='addtext'
                     && event.change['target.className'].indexOf(actions[rule]['target'])>=0
                 ) {
                    fire_rule(mutation, event, actions, rule);
                    break;
                }
                else if (is_string(event.change['target.parentNode.className'])
                         && event.change['target.parentNode.className'].indexOf(actions[rule]['target'])>=0
                        ) {
                    fire_rule(mutation, event, actions, rule);
                    break;
                }
            }
        });
    });
    return observer;
}

// Set mutation observer options
var MUTATION_OBSERVER_OPTIONS = {
    // We don't want to watch attribute changes
    attributes: false,

    // but we do want to watch tree and character changes.
    childList: true,
    characterData: true,
    subtree: true
};

// OK, now create the MutationObserver and start running it
// on the document.
observer = prepare_mutation_observer();
observer.observe(editor, MUTATION_OBSERVER_OPTIONS);

/*
   Document Load Code Block
*/
function writing_onload() {
    if(this_is_a_google_doc()) {
        log_event("document_loaded", {
            "partial_text": google_docs_partial_text()
        })
        execute_on_page_space("_docs_flag_initialData.info_params.token")
        const handleFromWeb = async (event) => {
            if (event.data.from && event.data.from === "inject.js") {
                const data = event.data.data;
                var token = JSON.parse(data);
                google_docs_version_history(token);
            }
        };
    
        window.addEventListener('message', handleFromWeb);
    }
}

/*
This is code which, if executed on the page space, will capture HTTP
AJAX responses.

This is impossible to do directly from within an extension.

This is currently unused.
*/
const LOG_AJAX = "\n\
const WO_XHR = XMLHttpRequest.prototype;\n\
const wo_send = WO_XHR.send;\n\
\n\
\n\
WO_XHR.send = function () {\n\
    this.addEventListener('load', function () {\n\
        console.log(this); console.log(this.getAllResponseHeaders());\n\
    }); return wo_send.apply(this, arguments); }\n\
"

window.addEventListener("load", writing_onload);

// This event listener is to used to detect changes in the document's 
// visibility. E.g. when a user switches tabs and back.
window.addEventListener("visibilitychange", () => {
    if (!document.hidden) {
        console.log("I got reloaded again...")
    }
});
