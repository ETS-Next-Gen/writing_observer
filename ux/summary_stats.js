const LENGTH = 30;

const width = 960;
const height = 500;
const margin = 5;
const padding = 5;
const adj = 30;

export const name = 'summary_stats';

export function summary_stats(div) {
    var svg = div.append("svg")
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

    data = {
	'Active Time': 901,
	'Date Started': 5,
	'Characters Typed': 4065,
	'Text Complexity': 8,
	'Time Since Last Edit': 3,
	'Word Count': 678
    };
    
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
    
    return svg;
}

d3.select("#debug_testing_summary").call(summary_stats).call(console.log);
