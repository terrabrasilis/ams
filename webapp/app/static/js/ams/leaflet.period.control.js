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

        let info = L.DomUtil.create('div', className+'-form '+className+'-info ');
        let select='<select name="numdays" id="numdays">'
        +'<option value="7">7 dias</option>'
        +'<option value="15">15 dias</option>'
        +'<option value="30">30 dias</option>'
        +'<option value="90">90 dias</option>'
        +'<option value="365">365 dias</option>'
        +'</select>';
        info.innerHTML='Controle da unidade temporal - '+select+' ';
        container.appendChild(info);

        let form = L.DomUtil.create('div', className+'-form');
        form.innerHTML='<i onclick="ams.PeriodHandler.previousPeriod()" '
        + 'title="Período anterior" '
        + 'class="material-icons icon-period-control noselect">chevron_left</i>'
        + '<label class="period-control">'
        + '<span class="period-control"> de </span>'
        + '<input type="text" id="datepicker-end" size="10" disabled '
        + 'title="Data inicial do período"/></label>'
        + '<label class="period-control">'
        + '<span class="period-control"> até </span>'
        + '<input type="text" id="datepicker-start" size="10" '
        + 'title="Data final do período - clique para alterar"/></label>'
        + '<i onclick="ams.PeriodHandler.nextPeriod()" '
        + 'title="Próximo período" id="next-period" style="visibility:hidden" '
        + 'class="material-icons icon-period-control noselect">chevron_right</i>';

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
		let datepicker = new ams.datepicker.Datepicker();
		$.datepicker.regional['br'] = datepicker.regional("br");
		$.datepicker.setDefaults($.datepicker.regional["br"]);

		$('#datepicker-start').datepicker({
			showButtonPanel: true,
			defaultDate: this.options.startDate,
			minDate: new Date("2017-01-01T00:00:00"),
			maxDate: this.options.startDate,
			changeMonth: true,
			changeYear: true,	
			todayBtn: "linked",	
			onSelect: function() {
				// changes the reference date used to the max date for displayed data
				let selected = $(this).val().split("/");
				let date = selected[2] + "-" + selected[1] + "-" + selected[0];
                ams.PeriodHandler.changeDate(date);
			},
			beforeShow: function() {
				setTimeout(function() {
					$('.ui-datepicker').css('z-index', 99999999999999);
				}, 0);
			}
		}).val(this.options.startDate.toLocaleDateString("pt-BR"));

        $('#datepicker-end').datepicker({
			showButtonPanel: true,
			defaultDate: ams.PeriodHandler._enddate,
			minDate: new Date("2017-01-01T00:00:00"),
			maxDate: ams.PeriodHandler._enddate,
			changeMonth: true,
			changeYear: true,	
			todayBtn: "linked"
		}).val(ams.PeriodHandler._enddate.toLocaleDateString("pt-BR"));

        // about new period selector
        $('#numdays').on('change',(ev)=>{
            let options=ev.target;
            let numdays;
            for (let i=0;i<options.length;i++){
                if(options[i].selected){
                    numdays=+options[i].value;
                    break;
                }
            }
            let obj={
                "acronym": ams.App._dateControl.getPeriodByDays(numdays),
                "name": "Agregado "+numdays+" dias",
                "group": {
                    "name": "UNIDADE TEMPORAL"
                }
            }
            // dispache event to update layers using selected filters
            ams.App._map.fire('changectrl', obj);
        });
        let numdays = ams.App._dateControl.getNumberOfDays();
        let options=$('#numdays')[0];
        for (let option in options){
            if(option.value==numdays)
                option.selected=true;
        }
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