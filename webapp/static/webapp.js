function decode_string_dict(stringdict) {
    /*
      Decode a string dictionary of the form:
        `key1=value1; key2=value2;key3=value3`
      This is used both to encode document hashes and for cookies.

      This is inspired by a (buggy) cookie decoder from w3cschools. We
      wrote out own since that one starts out with decodeURIComponent,
      potentially allowing for injections.
     */
    var decoded = {};
    var splitstring = stringdict.split(';');
    for(var i = 0; i<splitstring.length; i++) {
	var pair = splitstring[i];
	while (pair.charAt(0) == ' ') {
	    pair = pair.substring(1);
	}
	pair = pair.split('=');
	let key = decodeURIComponent(pair[0]);
	let value = decodeURIComponent(pair[1]);
	decoded[key] = value;
    }
    return decoded;
}

function getCookie(cookie_name) {
    /*
      Shortcut to grab a cookie. Return null if no cookie exists.
     */
    return decode_string_dict(document.cookie)[cookie_name];
}

function go_home() {
    /*
      Load the homepage.
     */
    window.location.href="/";
}

function error(error_message) {
    /*
      Show an error message.

      TODO: Do this at least somewhat gracefully.
     */
    alert("Error: "+error_message);
    go_home();
}

requirejs(
    ["/static/3rd_party/d3.v5.min.js",
     "/static/3rd_party/mustache.min.js",
     "/static/3rd_party/showdown.js",
     "/static/3rd_party/fontawesome.js",
     "/static/wobserver.js",
     "3rd_party/text!/static/modules/unauth.md",
     "3rd_party/text!/static/modules/login.html",
     "3rd_party/text!/static/modules/courses.html",
     "3rd_party/text!/static/modules/course.html",
     "3rd_party/text!/static/modules/navbar_loggedin.html",
     "3rd_party/text!/static/modules/informational.html",
    ],
    function(d3, mustache, showdown, fontawesome, wobserver, unauth, login, courses, course, navbar_li, info) {
	function load_login_page() {
	    d3.select(".main-page").html(login);
	}

	function load_courses_page() {
	    /*
	      Listing of Google Classroom courses
	      */
	    d3.select(".main-page").html(courses);
	    d3.json("/webapi/courselist/").then(function(data){
		/*
		  TODO: We want a function which does this abstracted
		  our. In essense, we want to call
		  d3.json_with_auth_and_errors
		*/
		if(data["error"]!=null) {
		    if(data["error"]["status"]==="UNAUTHENTICATED") {
			load_login_page();
		    }
		    else {
			error("Unknown error!");
		    }
		} else {
		    let cdg = d3.select(".awd-course-list");
		    cdg.selectAll("div.awd-course-card")
			.data(data)
			.enter()
			.append("div")
			.html(function(d) {
			    return mustache.render(course, d);
			});
		}
	    });
	}

	function load_dashboard_page(course) {
	    /*
	      Classroom writing dashboard
	     */
	    console.log(wobserver);
	    d3.select(".main-page").text("Loading Writing Observer...");
	    wobserver.initialize(d3, d3.select(".main-page"), course);
	}

	function load_unauthorized_page() {
	    /*
	      If an unauthenticated teacher logs in, we will show this
	      page.
	    */
	    sd = new showdown.Converter();
	    bodytext = sd.makeHtml(mustache.render(unauth, user_info()));
	    d3.select(".main-page").html(
		mustache.render(info,
				{text:bodytext}));

	}

	function user_info() {
	    let userinfo = JSON.parse(atob(getCookie("userinfo").replace('"', '').replace('"', '')));
	    //console.log(userinfo);
	    return userinfo;
	}

	function authenticated() {
	    // Decode user info.
	    // I hate web browsers. There seems to be a more-or-less random addition of quotes
	    // around cookies. Really.
	    return user_info() !== null;
	}

	function authorized() {
	    return user_info()['authorized'];
	}

	function decode_hash() {
	    let hash = location.hash;
	    if(hash.length === 0) {
		return false;
	    } else {
		return decode_string_dict(location.hash.slice(1));
	    }
	    //console.log("Unrecognized hash");
	    return false;
	}

	function loggedin_navbar_menu() {
	    d3.select(".main-navbar-menu").html(mustache.render(navbar_li, {
		'user_name': user_info()['name'],
		'user_picture': user_info()['picture']
	    }));
	}

	function setup_page() {
	    const hash_dict = decode_hash();
	    if(!authenticated()) {
		//console.log("Login page");
		load_login_page();
	    } else if(!authorized()) {
		load_unauthorized_page();
	    }
	    else if(!hash_dict) {
		//console.log("Courses page");
		load_courses_page();
		loggedin_navbar_menu()
	    } else if (hash_dict['tool'] === 'WritingObserver') {
		load_dashboard_page(hash_dict['course_id']);
		loggedin_navbar_menu()
	    } else {
		error("Invalid URL");
	    }
	}

	window.addEventListener('hashchange', function(){
	    setup_page();
	});

	setup_page()
    }
);
