import { deane_graph } from './deane.js'
import { student_text } from './text.js'
import { summary_stats } from './summary_stats.js'
import { outline } from './outline.js'

var student_data = [[1,2,3,4],[5,6,7,8],[9,10,11,12],[13,14,15,16],[17,18,19]];

const tile_template = document.getElementById('template-tile').innerHTML

function populate_tiles(tilesheet) {
    var rows=tilesheet.selectAll("div.wo-row-tile")
	.data(student_data)
	.enter()
	.append("div")
	.attr("class", "tile is-ancestor wo-row-tile");

    var cols=rows.selectAll("div.wo-col-tile")
	.data(function(d) { return d; })
	.enter()
	.append("div")
	.attr("class", "tile is-parent wo-col-tile wo-flip-container is-3")
	.html(function(d) {
	    return Mustache.render(tile_template, d);
	    /*{
		name: d.name,
		body: document.getElementById('template-deane-tile').innerHTML
	    });*/
	})
	.each(function(d) {
	    d3.select(this).select(".typing-text").call(
		student_text,
		d["stream_analytics.writing_analysis.reconstruct"].text);
	})
	.each(function(d) {
	    d3.select(this).select(".deane").call(
		deane_graph,
		d["stream_analytics.writing_analysis.reconstruct"].edit_metadata);
	})
	.each(function(d) {
	    d3.select(this).select(".summary").call(summary_stats, d);
	})
	.each(function(d) {
	    d3.select(this).select(".outline").call(outline, d);
	});
}

function select_tab(tab) {
    return function() {
	d3.selectAll(".tilenav").classed("is-active", false);
	d3.selectAll(".tilenav-"+tab).classed("is-active", true);
	d3.selectAll(".wo-tilebody").classed("is-hidden", true);
	d3.selectAll("."+tab).classed("is-hidden", false);
    }
};

var tabs = ["typing", "deane", "summary", "outline", "timeline", "contact"];
for(var i=0; i<tabs.length; i++) {
    d3.select(".tilenav-"+tabs[i]).on("click", select_tab(tabs[i]));
}

var ws = new WebSocket(`wss://${window.location.hostname}/wsapi/student-data/`)
ws.onmessage = function (event) {
    console.log("Got data");
    let data = JSON.parse(event.data);
    // dispatch
    if(data.logged_in === false) {
	console.log("Not logged in");
	d3.selectAll(".loading").classed("is-hidden", true);
        d3.selectAll(".auth-form").classed("is-hidden", false);
        d3.selectAll(".main").classed("is-hidden", true);
    } else if (data.new_student_data) {
	console.log("New data!");
	student_data = data.new_student_data;
        d3.selectAll(".loading").classed("is-hidden", true);
        d3.selectAll(".auth-form").classed("is-hidden", true);
        d3.selectAll(".main").classed("is-hidden", false);
	d3.select(".wo-tile-sheet").html("");
	d3.select(".wo-tile-sheet").call(populate_tiles);
    } else {
	console.log(data);
	console.log("Unrecognized JSON");
    }
};
