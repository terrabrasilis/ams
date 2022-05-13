/* global L */

// A period control that provides backwards and forwards between periods.
// Author: Andre Carvalho
L.Control.PeriodHandler = L.Control.extend({

    options: {
      position: 'bottomcenter',
      autoZIndex: true
    },
    _container:null,
  
    initialize: function (options) {
      L.Util.setOptions(this, options);
    },

    _initLayout: function (map) {
        let className='leaflet-period-control';
        let container = L.DomUtil.create('div', className);

        let form = L.DomUtil.create('div', className+'-form');
        form.innerHTML='<label class="leaflet-control-layers-group-name">'
        + '<span class="leaflet-control-layers-group-name"> de </span>'
        + '<input type="text" id="datepicker-end" size="7" disabled/></label>'
        + '<label class="leaflet-control-layers-group-name">'
        + '<span class="leaflet-control-layers-group-name"> até </span>'
        + '<input type="text" id="datepicker-start" size="7" /></label>';

        container.appendChild(form);

        $(container).mouseenter(function () {
            map.dragging.disable();
            map.scrollWheelZoom.disable();
            map.doubleClickZoom.disable();
        });
    
        $(container).mouseleave(function () {
            map.dragging.enable();
            map.scrollWheelZoom.enable();
            map.doubleClickZoom.enable();
        });
    
        if (L.Browser.touch) {
            L.DomEvent.on(container, 'click', L.DomEvent.stopPropagation);
        } else {
            L.DomEvent.disableClickPropagation(container);
            L.DomEvent.on(container, 'wheel', L.DomEvent.stopPropagation);
        }

        this._container=container;
    },

    _setDatepicker: function() {
        let defaultDate = new Date(this.options.startDate + "T00:00:00")
		let datepicker = new ams.datepicker.Datepicker();
		$.datepicker.regional['br'] = datepicker.regional("br");
		$.datepicker.setDefaults($.datepicker.regional["br"]);

		$('#datepicker-start').datepicker({
			showButtonPanel: true,
			defaultDate: defaultDate,
			minDate: new Date("2017-01-01T00:00:00"),
			maxDate: defaultDate,
			changeMonth: true,
			changeYear: true,	
			todayBtn: "linked",	
			onSelect: function() {
				// changes the reference date used to the max date for displayed data
				let selected = $(this).val().split("/");
				let date = selected[2] + "-" + selected[1] + "-" + selected[0];
				ams.App._dateControl.setPeriod(date, ams.App._currentTemporalAggregate);
				ams.App._suViewParams.updateDates(ams.App._dateControl);
				ams.App._priorViewParams.updateDates(ams.App._dateControl);
				ams.App._updateSpatialUnitLayer();
				ams.App._updateReferenceLayer();
                let enddate= new Date(ams.App._dateControl.enddate + "T00:00:00");
                $('#datepicker-end').datepicker().val(enddate.toLocaleDateString("pt-BR"));
			},
			beforeShow: function() {
				setTimeout(function() {
					$('.ui-datepicker').css('z-index', 99999999999999);
				}, 0);
			}
		}).val(defaultDate.toLocaleDateString("pt-BR"));

        let enddate= new Date(ams.App._dateControl.enddate + "T00:00:00");

        $('#datepicker-end').datepicker({
			showButtonPanel: true,
			defaultDate: enddate,
			minDate: new Date("2017-01-01T00:00:00"),
			maxDate: enddate,
			changeMonth: true,
			changeYear: true,	
			todayBtn: "linked"
		}).val(enddate.toLocaleDateString("pt-BR"));
    },
  
    onAdd: function (map) {
      this._initLayout(map);
      return this._container;
    },
  
    onRemove: function (map) {
        delete this._container;
    }
});

L.control.PeriodHandler = function (options) {
    return new L.Control.PeriodHandler(options);
};