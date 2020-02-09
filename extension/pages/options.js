/*
  Documentation on how to create an options page
 */

function saveServerToStorage(new_server) {
    console.log("Saving: "+new_server);
    chrome.storage.sync.set({
	"process-server": new_server
    }, restoreOptions);
}

function saveOptions(e) {
    /*
      Callback when user hits "save" on the options page
      */
    var new_server = document.querySelector("#process-server").value;
    saveServerToStorage(new_server);
    e.preventDefault();
}

function restoreOptions() {
    /*
      Initialize the options page for the extension. Eventually, we'd
      like to also use chrome.storage.managed so that school admins 
      can set these settings up centrally, without student overrides
     */
    chrome.storage.sync.get(['process-server'], function(result){
	var sync_storage_server = result['process-server'];
	console.log("Loaded saved server: " + sync_storage_server);
	if(!sync_storage_server) {
	    sync_storage_server = "writing.mitros.org";
	}
	document.querySelector("#current-process-server").innerText = sync_storage_server;
	document.querySelector("#process-server").value = sync_storage_server;
    });
}

document.addEventListener('DOMContentLoaded', restoreOptions);
document.querySelector("form").addEventListener("submit", saveOptions);
