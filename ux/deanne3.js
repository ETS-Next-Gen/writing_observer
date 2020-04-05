const LENGTH = 30;

const width = 960;
const height = 500;
const margin = 5;
const padding = 5;
const adj = 30;

function consecutive_array(n) {
    /* 
       This creates an array of length n [0,1,2,3,4...n] 
     */
    return Array(n).fill().map((e,i)=>i+1);
};

function randn_bm() {
    /* Approximately Gaussian distribution, mean 0.5
       From https://stackoverflow.com/questions/25582882/javascript-math-random-normal-distribution-gaussian-bell-curve */
    let u = 0, v = 0;
    while(u === 0) u = Math.random(); //Converting [0,1) to (0,1)
    while(v === 0) v = Math.random();
    let num = Math.sqrt( -2.0 * Math.log( u ) ) * Math.cos( 2.0 * Math.PI * v );
    num = num / 10.0 + 0.5; // Translate to 0 -> 1
    if (num > 1 || num < 0) return randn_bm(); // resample between 0 and 1
    return num;
}


function length_array(x) {
    /*
      Essay length
     */
    return x.map((e,i)=> (e*randn_bm(e) + e)/2);
}

function cursor_array(x) {
    /*
      Essay cursor position
     */
    var length_array = x.map((e,i)=> (e*Math.random()/2 + e*randn_bm()/2));
    return length_array;
}

function zip(a1, a2) {
    return a1.map(function(e, i) {
	return [e, a2[i]];
    });
}

function make_deanne_graph(div) {
    var svg = d3.select(div).append("svg")
      .attr("preserveAspectRatio", "xMinYMin meet")
      .attr("viewBox", "-"
            + adj + " -"
            + adj + " "
            + (width + adj *3) + " "
            + (height + adj*3))
      .style("padding", padding)
      .style("margin", margin)
      .style("border", "1px solid lightgray")
      .classed("svg-content", true);

    var x_edit = consecutive_array(LENGTH);
    var y_length = length_array(x_edit);
    var y_cursor = cursor_array(y_length);


    const yScale = d3.scaleLinear().range([height, 0]).domain([0, LENGTH])
    const xScale = d3.scaleLinear().range([0, width]).domain([0, LENGTH])


    var xAxis = d3.axisBottom(xScale)
	.ticks(4); // specify the number of ticks
    var yAxis = d3.axisLeft(yScale)
	.ticks(4); // specify the number of ticks

    svg.append('g')              // create a <g> element
	.attr("transform", "translate(0, "+height+")")
	.attr('class', 'x axis') // specify classes
	.call(xAxis);            // let the axis do its thing
    
    svg.append('g')              // create a <g> element
	.attr('class', 'y axis') // specify classes
	.call(yAxis);            // let the axis do its thing

    var lines = d3.line();

    var length_data = zip(x_edit.map(xScale), y_length.map(yScale));
    
    var cursor_data = zip(x_edit.map(xScale), y_cursor.map(yScale));
    
    var pathData = lines(length_data);
    
    svg.append('g')                           // create a <g> element
	.attr('class', 'essay-length lines')
	.append('path')
	.attr('d', pathData)
	.attr('fill', 'none')
	.attr('stroke', 'black')
	.attr('stroke-width','3');
    
    pathData = lines(cursor_data);
    
    svg.append('g')                           // create a <g> element
	.attr('class', 'essay-length lines')
	.append('path')
	.attr('d', pathData)
	.attr('fill', 'none')
	.attr('stroke', 'black')
	.attr('stroke-width','3');
}

make_deanne_graph("#deanne")
