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
    [requireconfig(),
     requireexternallib("d3.v5.min.js"),
     requireexternallib("mustache.min.js"),
     requireexternallib("showdown.js"),
     requireexternallib("fontawesome.js"),
     requiremodulelib("wobserver.js"),
     requiresystemtext("modules/navbar_loggedin.html"),
    ],
    function(config, d3, mustache, showdown, fontawesome, wobserver, navbar_li) {
	// Parse client configuration.
	config = JSON.parse(config);
	// Add libraries
	config.d3 = d3;
	config.ajax = ajax(config);
	function load_dashboard_page(course) {
	    /*
	      Classroom writing dashboard
	     */
	    console.log(wobserver);
	    d3.select(".main-page").text("Loading Writing Observer...");
	    wobserver.initialize(d3, d3.select(".main-page"), course, config);
	}

	function loggedin_navbar_menu() {
	    d3.select(".main-navbar-menu").html(mustache.render(navbar_li, {
		'user_name': user_info()['name'],
		'user_picture': user_info()['picture']
	    }));
	}

	function setup_page() {
	    const hash_dict = decode_hash();
	    if(!authenticated() || !authorized()) {
		go_home();
	    }
	    else if(!hash_dict) {
		go_home();
	    } else if (hash_dict['tool'] === 'WritingObserver') {
		load_dashboard_page(hash_dict['course_id']);
		loggedin_navbar_menu()
	    } else {
		error("Invalid URL");
	    }
	}
	setup_page();
    }
);
