// -------------------------------------------------------------------------------------------------------------------
// Top visualisation area configuration (category count)
// -------------------------------------------------------------------------------------------------------------------
function CategoryChart () {
	var margin = { top: 60, right: 10, bottom: 10, left: 40 },
		width = 960;
		height = 300,
		x = d3.scale.ordinal(),
		y = d3.scale.linear(),
		xAxis = d3.svg.axis().scale(x),
		yAxis = d3.svg.axis().scale(y).orient("left").ticks(5),
		selectedCategories = [],
		stillSelecting = 0,
		event = d3.dispatch("selected"),
		topToBottom = false;

	function chart(selection) {
		selection.each(function(data) {
			// Order data by category count
			data = data.sort(function (c1, c2) { return c1.count - c2.count; });

			// Trim categories that no longer exist
			selectedCategories = selectedCategories
				.filter(function (cat) {
					return data.some(function (c, i, arr) {
						return cat.id == c.id;
					});
				});

			// Update the x scale
			x.rangeBands([0, width - margin.left - margin.right], 0.1)
				.domain(data.map(function(cat) { return cat.category; }));

			// Update the y scale (add 10 percent space for the count labels)
    		y.range((topToBottom) ? [0, height - margin.top - margin.bottom] : [height - margin.top - margin.bottom, 0])
    			.domain([0, 1.10 * d3.max(data, function (cat) { return cat.count; })])
    			.nice();

    		// Select the svg element, if it exists
      		var svg = d3.select(this).selectAll("svg").data([data]);

      		// Otherwise, create the skeletal chart
      		var gEnter = svg.enter().append("svg").append("g").attr("transform", "translate(" + margin.left + "," + ((topToBottom) ? margin.top : margin.bottom) + ")");
      		gEnter.append("g").attr("class", "x axis");
      		gEnter.append("g").attr("class", "y axis");
      		gEnter.append("g").attr("class", "bars");

		    // Update the outer dimensions
		    svg.attr("width", width).attr("height", height);

		    // Update the containers position
		    svg.select("g").attr("transform", "translate(" + margin.left + "," + ((topToBottom) ? margin.top : margin.bottom) + ")");

			// De-select categories
			svg.selectAll("g.selectedBar").data(data).attr("class", "bar");

			// Remove extra bars
		    svg.selectAll("g.bar").data(data).exit().remove();

		    // Update existing bars
		    var bar = svg.selectAll("g.bar").data(data)
				.attr("transform", function(cat) { return "translate(" + x(cat.category) + ",0)"; });

			bar.select("rect")
				.attr("x", 0)
				.attr("y", (topToBottom) ? 1 : y.range()[0] - 1)
				.attr("width", x.rangeBand())
				.attr("height", 0)
				.transition().duration(2000)
				.attr("height", function(cat) { return topToBottom ? y(cat.count) : y.range()[0] - y(cat.count); })
				.attr("y", function(cat) { return topToBottom? 1 : y(cat.count) - 1; });

			bar.select("text") // count text
				.attr("x", x.rangeBand() / 2)
				.attr("y", (topToBottom) ? 10 : y.range()[0] - 10)
				.style("text-anchor", "middle")
				.text(function(cat) { return Math.floor(cat.count).toLocaleString(); })
				.transition().duration(2000)
				.attr("y", function(cat) { return y(cat.count) + ((topToBottom) ? 10 : -10); });

		    // Insert new bars
		    bar = svg.select("g.bars").selectAll("g.bar").data(data).enter()
		    	.append("g").attr("class", "bar")
				.attr("transform", function(cat) { return "translate(" + x(cat.category) + ",0)"; });

			bar.append("rect")
				.attr("x", 0)
				.attr("y", (topToBottom) ? 1 : y.range()[0] - 1)
				.attr("width", x.rangeBand())
				.attr("height", 0)
				.on("click", onClick)
				.transition().duration(2000)
				.attr("height", function(cat) { return topToBottom ? y(cat.count) : y.range()[0] - y(cat.count); })
				.attr("y", function(cat) { return topToBottom? 1 : y(cat.count) - 1; });

			bar.append("text") // count text
				.attr("class", "count_text")
				.attr("x", x.rangeBand() / 2)
				.attr("y", (topToBottom) ? 10 : y.range()[0] - 10)
				.style("text-anchor", "middle")
				.text(function(cat) { return Math.floor(cat.count).toLocaleString(); })
				.on("click", onClick)
				.transition().duration(2000)
				.attr("y", function(cat) { return y(cat.count) + ((topToBottom) ? 10 : -10); });

			// Re-select categories
			svg.selectAll("g.bar").attr("class", function (cat) {
				return (selectedCategories.some(function (c,i,arr) { return c.id == cat.id; })) ? "selectedBar" : "bar";
			});

	        // Update the x-axis
	        xAxis.orient((topToBottom) ? "top" : "bottom");
	      	svg.select(".x.axis").attr("transform", "translate(0," + y.range()[0] + ")")
	      		.call(xAxis)
	      	    .selectAll("text")
     			.style("text-anchor", "start")
     			.attr("dy", topToBottom ? "1.4em" : "0em")
     			.attr("dx", topToBottom ? "1.2em" : "1em")
     			.attr("transform", function(d) { return "rotate(" + (topToBottom ? -90 : 45) + ")"; });

	      	// Update the y-axis
	      	svg.select(".y.axis").call(yAxis);
		});
	}

	function onClick (cat)
	{
		var g = d3.select(this.parentElement);
		var index = function() {
				for (var i = 0; i < selectedCategories.length; i++)
					if (selectedCategories[i].id == cat.id)
						return i;
				return -1;
			}();

		// If already exists, remove from selection
		if (index >= 0)
		{
			selectedCategories.splice(index, 1);
			g.attr("class", "bar");
		}
		// If not add to selection
		else
		{
			selectedCategories.push(cat);
			g.attr("class", "selectedBar");
		}

		// Give a time window to select multiple categories without issuing a callback
		stillSelecting++;
		setTimeout(function() {
			if (--stillSelecting > 0)
				return;
			event.selected(selectedCategories);
		}, 2000);
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

    chart.topToBottom = function(value) {
    	if (!arguments.length) return topToBottom;
    	topToBottom = value;
    	return chart;
    };

	return d3.rebind(chart, event, "on");
}