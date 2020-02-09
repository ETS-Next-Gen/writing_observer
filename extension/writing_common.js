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

var writing_lasthash = "";
function unique_id() {
    /*
      This function is used to generate a (hopefully) unique ID for
      each event.
    */
    var shaObj = new jsSHA("SHA-256", "TEXT");
    shaObj.update(writing_lasthash);
    shaObj.update(Math.random().toString());
    shaObj.update(Date.now().toString());
    shaObj.update(document.cookie);
    shaObj.update("NaCl"); /* Salt? */
    shaObj.update(window.location.href);
    writing_lasthash = shaObj.getHash("HEX");
    return writing_lasthash;
}
