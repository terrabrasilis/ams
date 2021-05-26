var ams = ams || {};

ams.SLDStyles = {
	PercentageStyle: function(layerName, minValue, maxValue, onlyStrokes) {
		this.setStroke = function(onlyStrokes) {
			if(onlyStrokes) {
				this.fillOpacity = 0;
				this.stroke = '<Stroke>'
								+ '<CssParameter name="stroke">#ff0000</CssParameter>'
								+ '<CssParameter name="stroke-width">2</CssParameter>'
								+ '<CssParameter name="stroke-linejoin">bevel</CssParameter>'
							+ '</Stroke>';     
			}
		}

		this.setLegendDomainAndRange = function() {
			if(this.minValue < 0) {
				this.colorRange = ["#add8e6", "#f0f0f0", "#ff3838"];
				this.colorDomain = [this.minValue, 0, this.maxValue];
			}
			else {
				this.colorRange = ["#f0f0f0", "#ff3838"];
				this.colorDomain = [this.minValue, this.maxValue];
			}
		}

		this.stroke = "";
		this.fillOpacity = 1;
		this.setStroke(onlyStrokes);
		this.maxValue = maxValue;
		this.minValue = minValue;
		this.colorRange;
		this.colorDomain;

		this.createFill = function(value, color) {
			let fill = "";
			if(color) {
				let colorhex = d3.color(color).formatHex();
				fill = '<Fill><CssParameter name="fill">' + colorhex + '</CssParameter>';
				if(value == 0) {
					fill += '<CssParameter name="fill-opacity">0.1</CssParameter>';
				}
				fill += '</Fill>';
			}
			return fill;			
		}

		this.createTitle = function(v1, v2) {
			return  ((v1 < 0) ? '<Title>' : '<Title> ') + v1 + '% - ' + v2 + '% </Title>';
		}

		this.createFirstRule = function(v1, v2, color) {
			let fill = this.createFill(v1, color);
			return '<Rule>'
					+ this.createTitle(v1, v2)
					+ '<ogc:Filter>'
					+ 	'<ogc:PropertyIsLessThan>'
					+ 	'<ogc:PropertyName>percentage</ogc:PropertyName>'
					+ 	'<ogc:Literal>' + v2 + '</ogc:Literal>'
					+ 	'</ogc:PropertyIsLessThan>'
					+ '</ogc:Filter>'
					+ '<PolygonSymbolizer>' + fill + this.stroke + '</PolygonSymbolizer>'
				+ '</Rule>'; 			
		}

		this.createLastRule = function(v1, v2, color) {
			let fill = this.createFill(v1, color);
			return '<Rule>'
					+ this.createTitle(v1, v2)
					+ '<ogc:Filter>'
					+ 	'<ogc:PropertyIsGreaterThan>'
					+ 	'<ogc:PropertyName>percentage</ogc:PropertyName>'
					+ 	'<ogc:Literal>' + v1 + '</ogc:Literal>'
					+ 	'</ogc:PropertyIsGreaterThan>'
					+ '</ogc:Filter>'
					+ '<PolygonSymbolizer>' + fill + this.stroke + '</PolygonSymbolizer>'
				+ '</Rule>'; 			
		}		

		this.createRule = function(v1, v2, color) {
			let fill = this.createFill(v1, color);
			return '<Rule>'
					+ this.createTitle(v1, v2)
					+ '<ogc:Filter>'
					+	'<ogc:And>'
					+ 	'<ogc:PropertyIsGreaterThanOrEqualTo>'
					+ 	'<ogc:PropertyName>percentage</ogc:PropertyName>'
					+ 	'<ogc:Literal>' + v1 + '</ogc:Literal>'
					+ 	'</ogc:PropertyIsGreaterThanOrEqualTo>'
					+ 	'<ogc:PropertyIsLessThan>'
					+ 	'<ogc:PropertyName>percentage</ogc:PropertyName>'
					+ 	'<ogc:Literal>' + v2 + '</ogc:Literal>'
					+ 	'</ogc:PropertyIsLessThan>'
					+	'</ogc:And>'
					+ '</ogc:Filter>'
					+ '<PolygonSymbolizer>' + fill + this.stroke + '</PolygonSymbolizer>'
				+ '</Rule>';        
		} 

		this.getMaxLength = function(values) {
			let vMax = values[0].toString();
			let vMaxLength = vMax.length;
			for(let i = 1; i < values.length - 1; i++) {
				let v2 = values[i+1];
				let vlength = v2.toString().length;
				if(vlength > vMaxLength) {
					vMaxLength = vlength;
					vMax = v2.toString();
				}
			}
			if(vMax.includes(".")) {
				vMaxLength = vMax.split(".")[1].length;
			}
			return vMaxLength;
		}

		this.createRules = function(numOfRanges) {
			this.setLegendDomainAndRange();
			let legend = d3.scaleLinear()
				.domain(this.colorDomain)
				.range(this.colorRange)
				.nice(numOfRanges);
			let ticks = legend.ticks(numOfRanges);
			let rules = "";
			let firstRule = "";
			let lastRule = "";
			if(!onlyStrokes) {
				if(ticks.length >= 2) {			
					let vMaxLength = this.getMaxLength(ticks);
					firstRule = this.createFirstRule(ticks[0].toFixed(vMaxLength), 
												ticks[1].toFixed(vMaxLength), 
												legend(ticks[0]))
					for(let i = 1; i < ticks.length - 2; i++) {
						let v1 = ticks[i];
						let v2 = ticks[i+1];
						let color = legend(v1);
						rules = `${rules}${this.createRule(v1.toFixed(vMaxLength), 
															v2.toFixed(vMaxLength), 
															color)}`;
					}     
					let lastIdx = ticks.length - 1;
					lastRule = this.createLastRule(ticks[lastIdx - 1].toFixed(vMaxLength), 
												ticks[lastIdx].toFixed(vMaxLength), 
												legend(ticks[lastIdx - 1]));
				}
			}
			else {
				rules = `${rules}${this.createRule(ticks[0], ticks[ticks.length - 1])}`;
			}       

			return firstRule + rules + lastRule;   
		}

		this.sld = '<?xml version="1.0" encoding="ISO-8859-1"?>' 
					+ '<StyledLayerDescriptor version="1.0.0"'
					+ ' xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd"'
					+ ' xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc"'
					+ ' xmlns:xlink="http://www.w3.org/1999/xlink"' 
					+ ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
					+ '<NamedLayer><Name>' + layerName + '</Name>'
					+ '<UserStyle><Title>' + layerName + '</Title>'
					+ '<FeatureTypeStyle>' + this.createRules(6) + '</FeatureTypeStyle>'
					+ '</UserStyle></NamedLayer></StyledLayerDescriptor>'; 
		
		this.getSLD = function() {
			return this.sld;
		}
		this.getEncodeURI = function() {
			return encodeURIComponent(this.sld);
		}
	} 
};
