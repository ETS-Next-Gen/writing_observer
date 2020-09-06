//import { deane_graph } from './deane.js'
//import { student_text } from './text.js'
//import { summary_stats } from './summary_stats.js'
//import { outline } from './outline.js'

//var student_data = [[1,2,3,4],[5,6,7,8],[9,10,11,12],[13,14,15,16],[17,18,19]];

var tile_template;
var d3;

function populate_tiles(tilesheet) {
    /* Create rows for students */
    var rows=tilesheet.selectAll("div.wo-row-tile")
	.data(student_data)
	.enter()
	.append("div")
	.attr("class", "tile is-ancestor wo-row-tile");

    /* Create individual tiles */
    var cols=rows.selectAll("div.wo-col-tile")
	.data(function(d) { return d; })  // Propagate data down from the row into the elements
	.enter()
	.append("div")
	.attr("class", "tile is-parent wo-col-tile wo-flip-container is-3")
	.html(tile_template);

    /* Populate them with data */
    var cols_update=rows.selectAll("div.wo-col-tile")
	.data(function(d) { console.log(d); return d; })
    	.each(function(d) {
	    console.log(d.profile);
	    // Profile: Student name, photo, Google doc, phone number, email
	    d3.select(this).select(".wo-tile-name").text(d.profile.name.fullName);
	    d3.select(this).select(".wo-tile-photo").attr("src", d.profile.photoUrl);
	    d3.select(this).select(".wo-tile-email").attr("href", "mailto:"+d.profile.emailAddress);
	    d3.select(this).select(".wo-tile-phone").attr("href", "");          //
	    d3.select(this).select(".wo-tile-doc").attr("href", "");            //
	    // Summary stats: Time on task, time idle, and characters in doc
	    let reconstruct = d["stream_analytics.writing_analysis.reconstruct"];
	    let text = reconstruct.text;
	    d3.select(this).select(".wo-tile-character-count").select("span").text(text.length);
	    //d3.select(this).select(".wo-tile-character-count").select("rect").attr("width", 15);
	    let tot = d["stream_analytics.writing_analysis.time_on_task"];
	    d3.select(this).select(".wo-tile-total-time").select("span").text(tot["total-time-on-task"]);
	    //d3.select(this).select(".wo-tile-total-time").select("rect").attr("width", 15);
	    d3.select(this).select(".wo-tile-time-on-task").select("span").text("Hello");
	    //d3.select(this).select(".wo-tile-time-on-task").select("rect").attr("width", 15);
	    // Text
	    d3.select(this).select(".wo-tile-typing").text(text);
	});
}

var dashboard_template;
var Mustache;

function initialize(D3, div, course) {
    /*
      Populate D3 with the dashboard for the course
    */
    d3=D3;

    div.html(dashboard_template);
    var ws = new WebSocket(`wss://${window.location.hostname}/wsapi/writing-observer/${course}/`)
    ws.onmessage = function (event) {
	console.log("Got data");
	let data = JSON.parse(event.data);
	if(data.logged_in === false) {
	    window.location.href="/";  // TODO: System.go_home() or something
	} else if (data.new_student_data) {
	    console.log("New data!");
	    student_data = data.new_student_data;
	    d3.select(".wo-tile-sheet").call(populate_tiles, student_data);
            d3.selectAll(".wo-loading").classed("is-hidden", true);
	}

    /*
    var tabs = ["typing", "deane", "summary", "outline", "timeline", "contact"];
    for(var i=0; i<tabs.length; i++) {
	d3.select(".tilenav-"+tabs[i]).on("click", select_tab(tabs[i]));
    }

    ws.onmessage = function (event) {
	console.log("Got data");
	let data = JSON.parse(event.data);
	// dispatch

	} else {
	    console.log(data);
	    console.log("Unrecognized JSON");
	}
    };*/
    }
}

define(["3rd_party/text!/static/modules/dashboard.html",
	"3rd_party/text!/static/modules/tile.html",
        "/static/3rd_party/mustache.min.js",
       ],
       function(dashboard, tile, mustache) {
	   Mustache = mustache;
	   dashboard_template = dashboard;
	   tile_template = tile;
	   return {
	       "initialize": initialize
	   };
       });
