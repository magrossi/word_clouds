// ------------------------------------------------------------------------------
// Reusable time series charts - idea taken from http://bost.ocks.org/mike/chart/
// ------------------------------------------------------------------------------
function TimeSeriesChart() {
  if (!TimeSeriesChart.id) TimeSeriesChart.id = 0;

  var margin = {top: 5, right: 15, bottom: 20, left: 25},
      width = 760,
      height = 120,
      x = d3.time.scale(),
      y = d3.scale.linear(),
      xAxis = d3.svg.axis().scale(x).orient("bottom").tickSize(6, 0),
      yAxis = d3.svg.axis().scale(y).orient("left").tickSize(6, 0),
      area = d3.svg.area().x(function (d) { return x(d.date); }).y1(function (d) { return y(d.count); }),
      line = d3.svg.line().x(function (d) { return x(d.date); }).y(function (d) { return y(d.count); }),
      brush = d3.svg.brush().x(x).on('brush', onBrush).on('brushend', onBrushEnd),
      id = TimeSeriesChart.id++,
      customDomain = [],
      dataDomain = [],
      svg = undefined,
      showYAxis = true,
      showBrush = true,
      event = d3.dispatch("brush", "brushend"),
      areaClass = "area",
      lineClass = "line";

  function chart(selection) {
    selection.each(function(data) {
      // Update the x-scale.
      dataDomain = d3.extent(data, function (d) { return d.date; });
      x.domain((customDomain.length != 2) ? dataDomain : customDomain)
       .range([0, width - margin.left - margin.right]);

      // Update the y-scale.
      y.domain([0, 1.05 * d3.max(data, function (d) { return d.count; })]).nice()
       .range([height - margin.top - margin.bottom, 0]);

      // Select the svg element, if it exists.
      svg = d3.select(this).selectAll("svg").data([data]);

      // Otherwise, create the skeletal chart.
      var gEnter = svg.enter().append("svg").append("g");
      gEnter.append("clipPath").attr("id", "clip_" + id).append("rect").attr("width", width - margin.right - margin.left).attr("height", height - margin.bottom - margin.top);
      gEnter.append("path").attr("class", areaClass).style("clip-path", "url(#clip_" + id +")");
      gEnter.append("path").attr("class", lineClass).style("clip-path", "url(#clip_" + id +")");
      gEnter.append("g").attr("class", "x axis");
      gEnter.append("g").attr("class", "y axis");
      gEnter.append("g").attr("class", "x brush");

      // Update the outer dimensions.
      svg .attr("width", width)
          .attr("height", height);

      // Update the inner dimensions.
      var g = svg.select("g")
          .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

      // Update the area path.
      g.select("." + areaClass)
       .attr("d", area.y0(y.range()[0]));

      // Update the line path.
      g.select("." + lineClass)
       .attr("d", line);

      // Update the x-axis.
      g.select(".x.axis")
       .attr("transform", "translate(0," + y.range()[0] + ")")
       .call(xAxis);

      // Update the y-axis
      if (showYAxis)
        g.select(".y.axis").call(yAxis);

      // Update the brush
      UpdateBrush();
      });
  }

  function UpdateBrush()
  {
      // Update the brush
      if (showBrush && svg)
      {
        var g = svg.select("g");
        var gBrush = g.select(".x.brush");
        gBrush.call(brush);
        gBrush.selectAll("rect").attr("height", height - margin.top - margin.bottom);
        gBrush.selectAll(".resize")
          .append("path")
          .attr("transform", "translate(0,0)")
          .attr("d", resizePath);
      }
  }

  function resizePath (d)
  {
    var e = +(d == "e"),
        x = e ? 1 : -1,
        y = (height - margin.top - margin.bottom) / 3;
    return "M" + (.5 * x) + "," + y
        + "A6,6 0 0 " + e + " " + (6.5 * x) + "," + (y + 6)
        + "V" + (2 * y - 6)
        + "A6,6 0 0 " + e + " " + (.5 * x) + "," + (2 * y)
        + "Z"
        + "M" + (2.5 * x) + "," + (y + 8)
        + "V" + (2 * y - 8)
        + "M" + (4.5 * x) + "," + (y + 8)
        + "V" + (2 * y - 8);
  }

  function onBrush() {
    event.brush(brush.extent());
  }

  function onBrushEnd() {
    event.brushend(brush.extent());
  }

  chart.margin = function(value) {
    if (!arguments.length) return margin;
    margin = value;
    return chart;
  };

  chart.width = function(value) {
    if (!arguments.length) return width;
    width = value;
    return chart;
  };

  chart.height = function(value) {
    if (!arguments.length) return height;
    height = value;
    return chart;
  };

  chart.domain = function(value) {
    if (!arguments.length) return customDomain;
    customDomain = value;
    x.domain((customDomain.length != 2) ? dataDomain : customDomain);
    if (svg) {
      svg.select("." + areaClass).attr("d", area);
      svg.select("." + lineClass).attr("d", line);
      svg.select(".x.axis").call(xAxis);
    }
    return chart;
  };

  chart.showYAxis = function(value) {
    if (!arguments.length) return showYAxis;
    showYAxis = value;
    return chart;
  };

  chart.showBrush = function(value) {
    if (!arguments.length) return showBrush;
    showBrush = value;
    return chart;
  };

  chart.lineClass = function(value) {
    if (!arguments.length) return lineClass;
    lineClass = value;
    return chart;
  };

  chart.areaClass = function(value) {
    if (!arguments.length) return areaClass;
    areaClass = value;
    return chart;
  };

  chart.brushExtent = function (value) {
    if (!arguments.length) return brush.extent();
    brush.extent(value);
    UpdateBrush();
    onBrushEnd();
  };

  return d3.rebind(chart, event, "on");
}