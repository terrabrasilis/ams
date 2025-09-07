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
        this._setOptions(options);
    },

    _setOptions: function (options) {
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
            +'<option value="0">personalizado</option>'
            +'</select>';
        info.innerHTML='Controle da unidade temporal '+select+' ';
        container.appendChild(info);

        let form = L.DomUtil.create('div', className+'-form');
        form.innerHTML='<i id="previous-period" onclick="ams.PeriodHandler.previousPeriod()" '
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

    _setDatepicker: function(options) {
        if (options !== undefined) {
            this._setOptions(options);
        }
        let startDate = this.options.startDate;
        
        let datepicker = new ams.datepicker.Datepicker();
        $.datepicker.regional['br'] = datepicker.regional("br");
        $.datepicker.setDefaults($.datepicker.regional["br"]);

        function _validatePeriod() {
            let startDate = ams.Date.fromString($('#datepicker-start').val(), "dd/mm/yyyy");
            let endDate = ams.Date.fromString($('#datepicker-end').val(), "dd/mm/yyyy");
            return startDate >= endDate;
        }

        function _changeDate(val, datetype) {
            // changes the reference date used to the max date for displayed data
            let selected = val.split("/");
            let date = ams.Date.fromString(selected[2] + "-" + selected[1] + "-" + selected[0]);

            if (datetype == "end") {
                date.setUTCDate(date.getUTCDate() - 1);
            }

            ams.PeriodHandler.changeDate(ams.App._dateControl.toUTCDate(date), datetype);
        }

        function _updateCustomPeriod() {
            let startDate = $('#datepicker-start').val().split("/");
            
            let tmpDate = $('#datepicker-end').val().split("/");
            let endDate = ams.Date.fromString(tmpDate[2] + "-" + tmpDate[1] + "-" + tmpDate[0]);

            endDate.setDate(endDate.getDate() - 1);            

            // In the custom period mode the end date is 
            ams.App._dateControl.setCustomPeriod(
                startDate[2] + "-" + startDate[1] + "-" + startDate[0],
                endDate.toISOString().substr(0,10),
                1
            );
        }

        $('#datepicker-start').datepicker({
            showButtonPanel: true,
            defaultDate: this.options.startDate,
            minDate: new Date("2017-01-01T00:00:00"),
            maxDate: ams.PeriodHandler._maxdate,
            changeMonth: true,
            changeYear: true,    
            todayBtn: "linked",    
            onSelect: function() {
                _changeDate($(this).val(), "start")
            },
            beforeShow: function() {
                setTimeout(function() {
                    $('.ui-datepicker').css('z-index', 99999999999999);
                }, 0);
            }
        }).val(startDate.toLocaleDateString("pt-BR"));

        $('#datepicker-start').on('blur', function() {
            const value = $(this).val();
            _changeDate(value, "start");
        });

        $('#datepicker-end').datepicker({
            showButtonPanel: true,
            defaultDate: ams.PeriodHandler._enddate,
            minDate: new Date("2017-01-01T00:00:00"),
            maxDate: ams.PeriodHandler._enddate,
            changeMonth: true,
            changeYear: true,    
            todayBtn: "linked",
            onSelect:  function() {
                _changeDate($(this).val(), "end");
            },
        }).val(ams.PeriodHandler._enddate.toLocaleDateString("pt-BR"));

        $('#datepicker-end').on('blur', function() {
            const value = $(this).val();
            _changeDate(value, "end");
        });
        
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

            let custom = numdays === 0;

            if (!custom && ams.App._dateControl.getPeriod() === "custom") {
                ams.App._dateControl.disableCustomPeriod();
            }
            
            $("#datepicker-end").attr("disabled", !custom);

            let maxDate = custom? new Date(startDate - 1) : ams.PeriodHandler._enddate;
            $('#datepicker-end').datepicker("option", "maxDate", maxDate);

            if (custom) {
                let startDate = ams.Date.fromString($('#datepicker-start').val(), "dd/mm/yyyy");
                let endDate = ams.Date.fromString($('#datepicker-end').val(), "dd/mm/yyyy");
                numdays = ams.Date.differenceInDays(endDate, startDate);
                _updateCustomPeriod();
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
        let numdays = ams.App._dateControl.getPeriod() === "custom"? 0 : ams.App._dateControl.getNumberOfDays();
        let form_options = $('#numdays')[0];
        for (let i=0; i < form_options.length; ++i) {
            if(form_options[i].value==numdays)
                form_options[i].selected=true;
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
