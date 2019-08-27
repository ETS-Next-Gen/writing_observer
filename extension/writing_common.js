var WRITINGJS_SERVER = "https://test.mitros.org/webapi/";

function writingjs_ajax(data) {
    /*
      Helper function to send a logging AJAX request to the server.
      This function takes a JSON dictionary of data.

      TODO: Convert to a queue for offline operation using Chrome
      Storage API? Cache to Chrome Storage? Chrome Storage doesn't
      support meaningful concurrency,
     */

    httpRequest = new XMLHttpRequest();
    //httpRequest.withCredentials = true;
    httpRequest.open("POST", WRITINGJS_SERVER);
    httpRequest.send(JSON.stringify(data));
}


function googledocs_id_from_url(url) {
    /*
      Given a URL like:
        https://docs.google.com/document/d/jkldfhjklhdkljer8934789468976sduiyui34778dey/edit/foo/bar
      extract the associated document ID:
        jkldfhjklhdkljer8934789468976sduiyui34778dey
      Return null if not a valid URL
    */
    var match = url.match(/.*:\/\/docs\.google\.com\/document\/d\/([^\/]*)\/.*/i);
    if(match) {
	return match[1];
    }
    return null;
}

