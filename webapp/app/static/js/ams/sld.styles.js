var ams = ams || {};

ams.SLDStyles = {
	AreaStyle: function(layerName, propertyName, minValue, maxValue,
								isPriorization, priorColorHex) {

		let unit = "focos";
		if (propertyName == "area") {
		unit = "km²"; // default if auto is disabled
			if (ams.Config.general.area.changeunit == "auto") {
				let diff =
				minValue >= 0 ? maxValue - minValue : maxValue + minValue * -1;
				if (diff <= ams.Config.general.area.threshold) {
				unit = "ha";
				minValue = minValue * 100;
				maxValue = maxValue * 100;
				}
			}
		}

		if (ams.App._suViewParams.classname == "RK") {
			unit = "risco";
		}

		if (ams.App._suViewParams.classname == "RI") {
			unit = "score";
		}

		this.stroke = "";
		this.fillOpacity = 1;
		this.maxValue = maxValue;
		this.minValue = minValue;
		this.colorRange;
		this.colorDomain;
		this._unit = unit;
		this._propertyName = propertyName;
		this._numberOfTicks = 0;
		this._numberOfTicksN = 0;
		this._numberOfTicksP = 0;

		// if unit for area changes, raise notice and set globally
		if (ams.Map.PopupControl._unit !== unit) {
			let text = "", prefix = "";
			switch (unit) {
				case "focos":
					text = "número de focos";
					prefix = "Contagem: ";
					break;
				case "ha":
					text = "área (ha)";
					prefix = "Valor do indicador: ";
					break;
				case "km²":
					text = "área (km²)";
					prefix = "Valor do indicador: ";
					break;
				case "risco":
					text = "pontos de risco";
					prefix = "Contagem: ";
					break;
				case "score":
					text = "0 (sem risco) e 1 (maior risco)"
					prefix = "Intensidade de risco: "
			}

			if (text !== "") {
				$(".toast").toast("show");
				$(".toast-body").html(
				`Atenção, a unidade de medida foi alterada. ${prefix} ${text}.`
				);
				ams.Map.PopupControl._unit = unit;
				ams.Map.PopupControl._text = text;
				ams.Map.PopupControl._prefix = prefix;
			}
		}		  

		this.setStroke = function(isPriorization) {
			if(isPriorization) {
				this.fillOpacity = 0;
				this.stroke = '<Stroke>'
								+ '<CssParameter name="stroke">' 
								+ priorColorHex + '</CssParameter>'
								+ '<CssParameter name="stroke-width">2</CssParameter>'
								+ '<CssParameter name="stroke-linejoin">bevel</CssParameter>'
							+ '</Stroke>';     
			}
		}
		// change fill and stroke by priorization
		this.setStroke(isPriorization);

		this.setLegendDomainAndRange = function() {
			if(this.minValue < 0) {
				this.colorRange = ["#add8e6", "#f0f0f0", "#ff3838"];
				this.colorDomain = [this.minValue, 0, this.maxValue];
				this.colorRangeN = ["#add8e6", "#f0f0f0"];
				this.colorRangeP = ["#f0f0f0", "#ff3838"];
				this.colorDomainN = [this.minValue, 0];
				this.colorDomainP = [0, this.maxValue];
				let tn=Math.floor( Math.abs(this.minValue)/2);
				this._numberOfTicksN = ( (tn<5)?(tn):(5) );//5;
				let tp=Math.ceil(this.maxValue/2);
				this._numberOfTicksP = ( (tp<6)?(tp):(5) );//6;
			}
			else {
				this.colorRange = ["#f0f0f0", "#ff3838"];

				if (this._unit == "score") {
					let sf = 10;
					this.minValue = Math.max(0, Math.floor(this.minValue*sf) / sf);
					this.maxValue = Math.min(1, Math.ceil(this.maxValue*sf) / sf);
					
					this._numberOfTicks = (this.maxValue - this.minValue) * sf;

					if (this._numberOfTicks < 3) {
						this._numberOfTicks = 3;
						if (this.maxValue + 1. / sf > 1) {
							this.minValue = this.minValue - 1. / sf;
						} else {
							this.maxValue = this.maxValue + 1. / sf;
						}
					}

					this.colorDomain = [this.minValue, this.maxValue];

				} else {
					this.colorDomain = [this.minValue, this.maxValue];
					let tt=Math.ceil(this.maxValue);
					this._numberOfTicks = ( (tt<10)?(tt==1?2:tt):(10) );
				}
			}
		}

		this.createFill = function(value, color) {
			let fill = "";
			if(color) {
				let colorhex = d3.color(color).formatHex();
				fill = '<Fill><CssParameter name="fill">' + colorhex + '</CssParameter>';
				if(value == 0) {
					fill += '<CssParameter name="fill-opacity">0.5</CssParameter>';
				}
				fill += '</Fill>';
			}
			return fill;			
		}

		this._formatValue = function(v, vMaxLength) {
			v=(v=="-0"?"0":v);
			let vs = v.toString();
			let prefix = sufix = "";
			if(vs.includes(".")) {
				vs = vs.split(".")[0];
			}else{
				sufix = (this._unit=='ha')?(""):("   ");
			}
			if(vs.includes("-")) {
				prefix = " ";
			}					
			prefix += "  ".repeat(vMaxLength - vs.length);
			return prefix + v + sufix;
		}

		this.createTitle = function(v1, v2, vMaxLength) {
			return  '<Title>'
					+ ' de ' + this._formatValue(v1, vMaxLength)
					+ ' até ' + this._formatValue(v2, vMaxLength)
					+ ' </Title>';
		}

		this.createFirstRule = function(v1, v2, color, vMaxLength) {
			let fill = this.createFill(v1, color);
			let l2 = (this._unit=='ha')?(v2/100):(v2);
			return '<Rule>'
					+ this.createTitle(v1, v2, vMaxLength)
					+ '<ogc:Filter>'
					+ 	'<ogc:PropertyIsLessThanOrEqualTo>'
					+ 	'<ogc:PropertyName>' + this._propertyName + '</ogc:PropertyName>'
					+ 	'<ogc:Literal>' + l2 + '</ogc:Literal>'
					+ 	'</ogc:PropertyIsLessThanOrEqualTo>'
					+ '</ogc:Filter>'
					+ '<PolygonSymbolizer>' + fill + this.stroke + '</PolygonSymbolizer>'
				+ '</Rule>';
		}

		this.createLastRule = function(v1, v2, color, vMaxLength) {
			let fill = this.createFill(v1, color, vMaxLength);
			let l1 = (this._unit=='ha')?(v1/100):(v1);
			return '<Rule>'
					+ this.createTitle(v1, v2, vMaxLength)
					+ '<ogc:Filter>'
					+ 	'<ogc:PropertyIsGreaterThan>'
					+ 	'<ogc:PropertyName>' + this._propertyName + '</ogc:PropertyName>'
					+ 	'<ogc:Literal>' + l1 + '</ogc:Literal>'
					+ 	'</ogc:PropertyIsGreaterThan>'
					+ '</ogc:Filter>'
					+ '<PolygonSymbolizer>' + fill + this.stroke + '</PolygonSymbolizer>'
				+ '</Rule>'; 			
		}		

		this.createRule = function(v1, v2, color, vMaxLength) {
			let fill = this.createFill(v1, color);
			let l1 = (this._unit=='ha')?(v1/100):(v1);
			let l2 = (this._unit=='ha')?(v2/100):(v2);
			return '<Rule>'
					+ this.createTitle(v1, v2, vMaxLength)
					+ '<ogc:Filter>'
					+	'<ogc:And>'
					+ 	'<ogc:PropertyIsGreaterThan>'
					+ 	'<ogc:PropertyName>' + this._propertyName + '</ogc:PropertyName>'
					+ 	'<ogc:Literal>' + l1 + '</ogc:Literal>'
					+ 	'</ogc:PropertyIsGreaterThan>'
					+ 	'<ogc:PropertyIsLessThanOrEqualTo>'
					+ 	'<ogc:PropertyName>' + this._propertyName + '</ogc:PropertyName>'
					+ 	'<ogc:Literal>' + l2 + '</ogc:Literal>'
					+ 	'</ogc:PropertyIsLessThanOrEqualTo>'
					+	'</ogc:And>'
					+ '</ogc:Filter>'
					+ '<PolygonSymbolizer>' + fill + this.stroke + '</PolygonSymbolizer>'
				+ '</Rule>';        
		} 

		this._countOnRight = function(v) {
			let vs = v.toString();
			if(vs.includes(".")) {
				vs = vs.split(".")[0];
			}		
			return vs.length;
		}

		this.getMaxLength = function(values) {
			let vMaxLength = this._countOnRight(values[0]);
			for(let i = 1; i < values.length; i++) {
				let vlength = this._countOnRight(values[i]);
				if(vlength > vMaxLength) {
					vMaxLength = vlength;
				}
			}
			return vMaxLength;
		}

		this._getTickStep = function(domain, numberOfTicks) {
			return (domain[domain.length-1] - domain[0]) / (numberOfTicks - 1);
		}

		this._getTicks = function(domain, tickStep, numberOfTicks) {
			let ticks = [];
			ticks.push(domain[0])
			for(let i = 1; i < numberOfTicks; i++) {
				ticks.push(ticks[i-1] + tickStep);
			}
			return ticks;
		}

		this.createRules = function() {
			this.setLegendDomainAndRange();
			let legend = d3.scaleLinear()
				.domain(this.colorDomain)
				.range(this.colorRange);	

			let ticks;
			if(this.minValue == 0) {
				let domain = legend.domain();
				let tickStep = this._getTickStep(domain, this._numberOfTicks);
				ticks = this._getTicks(domain, tickStep, this._numberOfTicks);
			}
			else {
				let legendN = d3.scaleLinear()
					.domain(this.colorDomainN)
					.range(this.colorRangeN);	
				let legendP = d3.scaleLinear()
					.domain(this.colorDomainP)
					.range(this.colorRangeP);	
				let domainN = legendN.domain();						
				let domainP = legendP.domain();						
				let tickStepN = this._getTickStep(domainN, this._numberOfTicksN);
				let tickStepP = this._getTickStep(domainP, this._numberOfTicksP);
				let ticksN = this._getTicks(domainN, tickStepN, this._numberOfTicksN);
				let ticksP = this._getTicks(domainP, tickStepP, this._numberOfTicksP);
				for(let i = 1; i < ticksP.length; i++) {
					ticksN.push(ticksP[i]);
				}
				ticks = ticksN;
			}
			let rules = "";
			let firstRule = "";
			let lastRule = "";

			if(!isPriorization) {
				let fixedValue = ( (this._propertyName=='area' || this._propertyName=='score')?(1):(0) );
				for (let t in ticks) {
					ticks[t] = +(ticks[t].toFixed(fixedValue));
				}
				if(ticks.length >= 2) {
					let vMaxLength = this.getMaxLength(ticks);
					firstRule = this.createFirstRule(ticks[0], 
												ticks[1], 
												legend(ticks[0]), vMaxLength)
					for(let i = 1; i < ticks.length - 2; i++) {
						let v1 = ticks[i];
						let v2 = ticks[i+1];
						let color = legend(v1);
						rules = `${rules}${this.createRule(v1, 
															v2, 
															color, vMaxLength)}`;
					}     
					let lastIdx = ticks.length - 1;
					lastRule = this.createLastRule(ticks[lastIdx - 1], 
												ticks[lastIdx], 
												legend(ticks[lastIdx - 1]), vMaxLength);
				}
			}
			else {
				rules = `${rules}${this.createLastRule(this.minValue, this.maxValue)}`;
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
					+ '<FeatureTypeStyle>' + this.createRules() + '</FeatureTypeStyle>'
					+ '</UserStyle></NamedLayer></StyledLayerDescriptor>'; 
		
		this.getSLD = function() {
			return this.sld;
		}
		this.getEncodeURI = function() {
			return encodeURIComponent(this.sld);
		}
	}
};
