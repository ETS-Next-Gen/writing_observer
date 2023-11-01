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

import * as loEvent from 'lo_event/lo_event/lo_event.js';
import * as loEventDebug from 'lo_event/lo_event/debugLog.js';
import { websocketLogger } from 'lo_event/lo_event/websocketLogger.js';
import { consoleLogger } from 'lo_event/lo_event/consoleLogger.js';
import * as loEventUtils from 'lo_event/lo_event/util.js';

// We would like to support fetching the websocket server from storage

// callback = new Promise((resolve, reject) => {
//    storage.getItem('server').then((data) => resolve(data)
// } /* and other async logic */);
// websocketLogger( callback );

// We are not sure if this should be done within `websocketLogger()`'s `init`
// or one level up. 
const loggers = [
  consoleLogger(),
  websocketLogger(WEBSOCKET_SERVER_URL)
]

loEvent.init('org.mitros.writing_analytics', '0.01', loggers, loEventDebug.LEVEL.SIMPLE);
loEvent.setFieldSet([loEventUtils.getBrowserInfo(), loEventUtils.debuggingMetadata()]);
loEvent.go()

// Function to serve as replacement for 
// chrome.extension.getBackgroundPage().console.log(event); because it is not allowed in V3
// It logs the event to the console for debugging.
function logFromServiceWorker(event) {
  console.log(event);
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
        loEvent.logEvent(request['event'], request);
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
            loEvent.logEvent('raw_http_request', {
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
                loEvent.logEvent('google_docs_save', event);
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
                loEvent.logEvent('google_docs_save_extra', event);
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
loEvent.logEvent("extension_loaded", {});

// Send the server the user info. This might not always be available.
// HACK: this code will be changed pending server side changes to how we
// handle auth and metadata.
loEventUtils.profileInfoWrapper().then((result) => {
    if (Object.keys(result).length > 0) {
        loEvent.logEvent('chrome_identity', { chrome_identity: result });
        loEvent.logEvent('metadata_finished', {})
    }
});

// And let the console know we've loaded
// chrome.extension.getBackgroundPage().console.log("Loaded"); remove
logFromServiceWorker("Loaded");
