//
// This is the preloaded Learning Observer library.
//

// Path management, so that we can have relative URLs

function lo_modulepath(rel_path) {
    // This is used to retrieve URLs of relative
    // files in the same git repo.
    const path = new URL(document.URL).pathname;
    const last_slash = path.lastIndexOf("/");
    const base_path = path.slice(0, last_slash+1);
    return base_path + rel_path;
}

function lo_thirdpartypath(rel_path) {
    // This is used to retrieve URLs of external libraries
    return "/static/3rd_party/"+rel_path;
}

function requiremodulelib(lib) {
    return lo_modulepath(lib);
}

function requireexternallib(lib) {
    return lo_thirdpartypath(lib)
}

function requiremoduletext(text) {
    return "/static/3rd_party/text.js!"+lo_modulepath(text);
}

function requiresystemtext(text) {
    return "/static/3rd_party/text.js!/static/"+text
}

function requireconfig() {
    return "/static/3rd_party/text.js!/config.json";
}




// Helper functions.
//
//

function rendertime1(t) {
    /*
      Convert seconds to a time string.
         10     ==> 10 sec
	 120    ==> 2:00
	 3600   ==> 1:00:00
	 7601   ==> 2:06:41
	 764450 ==> 8 days

     */
    function str(i) {
        if(i<10) {
            return "0"+String(i);
        }
        return String(i)
    }
    var seconds = Math.floor(t) % 60;
    var minutes = Math.floor(t/60) % 60;
    var hours = Math.floor(t/3600) % 60;
    var days = Math.floor(t/3600/24);

    if ((minutes === 0) && (hours === 0) && (days === 0)) {
	return String(seconds) + " sec"           // 0-59 seconds
    }
    if (days>0) {
	return String(days) + " days"             // >= 1 day
    }
    if(hours === 0) {
	return String(minutes)+":"+str(seconds);  // 1 minute - 1 hour
    }
    return String(hours)+":"+str(minutes)+":"+str(seconds)  // 1 - 24 hours
}

function rendertime2(t) {
    /*
      Convert seconds to a time string.

      Compact representation.
         10     ==> 10s
	 125    ==> 2m
	 3600   ==> 1h
	 7601   ==> 2h
	 764450 ==> 8d

     */
    function str(i) {
        if(i<10) {
            return "0"+String(i);
        }
        return String(i)
    }
    var seconds = Math.floor(t) % 60;
    var minutes = Math.floor(t/60) % 60;
    var hours = Math.floor(t/3600) % 60;
    var days = Math.floor(t/3600/24);

    if(days>0) {
	return String(days)+'d';
    }
    if(hours>0) {
	return String(hours)+'h';
    }
    if(minutes>0) {
	return String(minutes)+'m';
    }
    if(seconds>0) {
	return String(seconds)+'s';
    }
    return '-';
}
