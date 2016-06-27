// -------------------------------------------------------------------------------------------------------------------
// Word cloud visualisation area
// -------------------------------------------------------------------------------------------------------------------
function WordCloud() {
	var colors = ['colorCat_1', 'colorCat_2', 'colorCat_3', 'colorCat_4', 'colorCat_5', 'colorCat_6'],
		margin = { top: 70, right: 10, bottom: 10, left: 40 },
		width = 960,
		height = 320,
		s = d3.scale.linear(),
		layout = d3.layout.cloud()
					.timeInterval(10)
					.spiral("archimedean") // archimedean or rectangular
					.padding(0.5)
					.rotate(function(d) { return d.term.length > 5 ? 0 : ~~(Math.random() * 2) * 90; })
					.font("Impact")
					.fontSize(function(d) { return s(Math.floor(+d.tf_idf)); })
					.text(function(d) { return d.term; })
					.on("end", draw),
		fill = d3.scale.quantize().range(colors),
		transitionTime = 2000,
		event = d3.dispatch("click", "cloudend"),
		maxWords = 100,
		wordsShowing = 0,
		fullWords = undefined,
		svg = undefined;

	function chart (selection) {
		// Do the charting
		selection.each(function(data) {		
			// Create the svg element if it doesnt exist
			svg = d3.select(this).selectAll("svg").data([data]);
			svg.enter().append("svg").append("g").attr("transform", "translate(" + [width >> 1, height >> 1] + ")");

			// Update the outer dimensions
			svg.attr("width", width).attr("height", height);//.attr('x', margin.left);

			// Refresh the layout size and scales
			layout.size([width, height]);
			s.range([20, 80]);
			fill.domain(s.range());

			// Calculate the x and y points for each word based on layout
			fullWords = data.slice(0, Math.min(maxWords, data.length - 1));

			// Refresh the word size calculator scale
			s.domain(d3.extent(fullWords, function (d) { return Math.floor(+d.tf_idf); }));

			// Fade out all existing words
			svg.selectAll("text").transition(transitionTime)
				.style("font-size", "1px")
				.style("opacity", 0)
				.attr("transform", "translate(0,0)");

			layout.stop().words(fullWords).start();
		});
	}

	function draw (words, bounds) {
		wordsShowing = words.length;

		var scale = bounds ? Math.min(width / Math.abs(bounds[1].x - width / 1), width / Math.abs(bounds[0].x - width / 1), height / Math.abs(bounds[1].y - height / 1), height / Math.abs(bounds[0].y - height / 1)) / 1 : 1;
		var g = svg.select("g");

		// Update existing texts
		var p = g.selectAll("text")
	        .data(words)
	        //.data(fullWords)
	        .attr("class", "");

		// Insert new texts
		p.enter().append("text")
		    .style("font-family", "Impact")
	        .attr("text-anchor", "middle")
	        .attr("class", "")
	        .on("click", onClick);

	    // Fade in the words
	    p.text(function(d) { return d.text; })
	    	.transition(transitionTime)
	        .style("font-size", function(d) { return d.size + "px"; })
	        .style("opacity", 1)
	        .attr("class", function(d) { return "cloudText " + fill(d.size); })
	        .attr("transform", function(d) { return "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")"; });

		// Delete extra texts
	    p.exit().remove();

	    // Scale the world cloud to show all words
		g.transition()
		   .delay(transitionTime)
		   .attr("transform", "translate(" + [width >> 1, height >> 1] + ")scale(" + scale + ")");

		onEnd();
	}

	function onClick (word) {
		event.click(word.text);
	}

	function onEnd ()
	{
		event.cloudend();
	}


	chart.margin = function (value) {
    	if (!arguments.length) return margin;
    	margin = value;
    	return chart;
    };

    chart.width = function (value) {
    	if (!arguments.length) return width;
    	width = value;
    	return chart;
    };

    chart.height = function (value) {
    	if (!arguments.length) return height;
    	height = value;
    	return chart;
    };

    chart.maxWords = function (value) {
    	if (!arguments.length) return maxWords;
    	maxWords = value;
    	return chart;
    };

    chart.wordsShowing = function() {
    	return wordsShowing;
    }

	return d3.rebind(chart, event, "on");
}