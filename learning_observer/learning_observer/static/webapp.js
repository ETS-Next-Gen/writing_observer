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

function ajax(config)
{
    return function(url) {
	// Do AJAX calls with error handling
	return new Promise(function(resolve, reject) {
	    config.d3.json(url)
		.then(function(data){
		    resolve(data);
		})
		.catch(function(data){
		    reject(data);
		});
	});
    }
}


requirejs(
    // TODO: Clean up absolute paths. We hardcoded these for now, due to refactor.
    ["/static/3rd_party/text.js!/config.json",
     "/static/3rd_party/text.js!/webapi/course_dashboards",  // Perhaps this belongs in config.json?
     "/static/3rd_party/d3.v5.min.js",
     "/static/3rd_party/mustache.min.js",
     "/static/3rd_party/showdown.js",
     "/static/3rd_party/fontawesome.js",
     "/static/3rd_party/text.js!/static/modules/unauth.md",
     "/static/3rd_party/text.js!/static/modules/login.html",
     "/static/3rd_party/text.js!/static/modules/courses.html",
     "/static/3rd_party/text.js!/static/modules/course.html",
     "/static/3rd_party/text.js!/static/modules/tool.html",
     "/static/3rd_party/text.js!/static/modules/navbar_loggedin.html",
     "/static/3rd_party/text.js!/static/modules/informational.html",
    ],
    function(config, tool_list, d3, mustache, showdown, fontawesome, unauth, login, courses, course, tool, navbar_li, info) {
	// Parse client configuration.
	config = JSON.parse(config);
	tool_list = JSON.parse(tool_list);
	// Add libraries
	config.d3 = d3;
	config.ajax = ajax(config);

	function password_authorize() {
	    d3.json("/auth/login/password", {
		method: 'POST',
		headers: {
		    "Content-type": "application/json; charset=UTF-8"
		},
		body: JSON.stringify({
		    username: d3.select(".lo-login-username").property("value"),
		    password: d3.select(".lo-login-password").property("value")
		})
	    }).then(function(data) {
		if (data['status'] === 'authorized') {
		    load_courses_page();
		} else if (data['status'] === 'unauthorized') {
		    // TODO: Flash a nice subtle message
		    alert("Invalid username or password!");
		}
		else {
		    console.log(data);
		}
	    });
	}

	function load_login_page() {
	    d3.select(".main-page").html(mustache.render(login, config['theme']));
	    d3.select(".lo-google-auth").classed("is-hidden", !config['google-oauth']);
	    d3.select(".lo-password-auth").classed("is-hidden", !config['password-auth']);
	    d3.select(".lo-login-button")
		.on("click", function() {
		    password_authorize();
		});
	}

	function load_courses_page() {
	    /*
	      Listing of Google Classroom courses
	      */
	    d3.select(".main-page").html(courses);
	    config.ajax("/webapi/courselist/").then(function(data){
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
			    let tools = "";
			    for(var i=0; i<tool_list.length; i++) {
				tool_list[i].icon = tool_list[i].icon.type +
				    " " +
				    tool_list[i].icon.icon;
				tools += mustache.render(tool, tool_list[i]);
			    }
			    d['tools'] = tools;
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
