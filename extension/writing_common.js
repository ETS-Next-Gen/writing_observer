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

