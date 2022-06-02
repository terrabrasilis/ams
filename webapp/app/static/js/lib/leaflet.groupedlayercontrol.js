/* global L */

// A layer control which provides for layer groupings.
// Author: Ishmael Smyrnow
L.Control.GroupedLayers = L.Control.extend({

  options: {
    collapsed: true,
    position: 'topright',
    autoZIndex: true,
    exclusiveGroups: [],
    groupCheckboxes: false
  },

  initialize: function (controlGroups, options) {
    var i, j;
    L.Util.setOptions(this, options);

    this._ctrls = [];
    this._groupList = [];
    this._domGroups = [];

    for (i in controlGroups) {
      for (j in controlGroups[i]) {
        if(j=='defaultFilter' || j=='propertyName') continue;
        this._addControl(controlGroups[i][j], j, i, controlGroups[i]['defaultFilter'], true);
      }
    }
  },

  onAdd: function (map) {
    this._initLayout(map);
    this._update();
    return this._container;
  },

  onRemove: function (map) {
  },

  _getControlById: function (id) {
    for (var i = 0; i < this._ctrls.length; i++) {
      if (this._ctrls[i] && this._ctrls[i].ctrlId === id) {
        return this._ctrls[i];
      }
    }
  },

  _initLayout: function (map) {
    var className = 'leaflet-control-layers',
      container = this._container = L.DomUtil.create('div', className);

    // Makes this work on IE10 Touch devices by stopping it from firing a mouseout event when the touch is released
    container.setAttribute('aria-haspopup', true);

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

    var form = this._form = L.DomUtil.create('form', className + '-list');

    this._baseLayersList = L.DomUtil.create('div', className + '-base', form);
    this._separator = L.DomUtil.create('div', className + '-separator', form);
    this._overlaysList = L.DomUtil.create('div', className + '-overlays', form);

    container.appendChild(form);

    if (this.options.collapsed) {
      if (!L.Browser.android) {
        L.DomEvent
            .on(container, 'mouseover', this._expand, this)
            .on(container, 'mouseout', this._collapse, this);
      }
      var link = this._layersLink = L.DomUtil.create('a', className + '-toggle', container);
      link.href = '#';
      link.title = 'Layers';

      if (L.Browser.touch) {
        L.DomEvent
            .on(link, 'click', L.DomEvent.stop)
            .on(link, 'click', this._expand, this);
      } else {
        L.DomEvent.on(link, 'focus', this._expand, this);
      }

      this._map.on('click', this._collapse, this);
      // TODO keyboard accessibility
    } else {
      this._expand();
    }
  },

  _addControl: function (acronym, name, group, defaultFilter, overlay) {
    var _ctrl = {
      acronym: acronym,
      name: name,
      defaultFilter: defaultFilter,
      overlay: overlay
    };
    _ctrl["ctrlId"]=L.Util.stamp(_ctrl);
    this._ctrls.push(_ctrl);

    group = group || '';
    var groupId = this._indexOf(this._groupList, group);

    if (groupId === -1) {
      groupId = this._groupList.push(group) - 1;
    }

    var exclusive = (this._indexOf(this.options.exclusiveGroups, group) !== -1);

    _ctrl.group = {
      name: group,
      id: groupId,
      exclusive: exclusive
    };
  },

  _update: function () {
    if (!this._container) {
      return;
    }

    this._baseLayersList.innerHTML = '';
    this._overlaysList.innerHTML = '';
    this._domGroups.length = 0;

    var baseLayersPresent = false,
      overlaysPresent = false,
      i, obj;

    for (var i = 0; i < this._ctrls.length; i++) {
      obj = this._ctrls[i];
      this._addItem(obj);
      overlaysPresent = overlaysPresent || obj.overlay;
      baseLayersPresent = baseLayersPresent || !obj.overlay;
    }

    this._separator.style.display = overlaysPresent && baseLayersPresent ? '' : 'none';
  },

  // IE7 bugs out if you create a radio dynamically, so you have to do it this hacky way (see http://bit.ly/PqYLBe)
  _createRadioElement: function (name, checked) {
    var radioHtml = '<input type="radio" class="leaflet-control-layers-selector" name="' + name + '"';
    if (checked) {
      radioHtml += ' checked="checked"';
    }
    radioHtml += '/>';

    var radioFragment = document.createElement('div');
    radioFragment.innerHTML = radioHtml;

    return radioFragment.firstChild;
  },

  _addItem: function (obj) {
    // for initial state of checked control, use the ams.Config.defaultFilters defines...

    var label = document.createElement('label'),
      input,
      checked = obj.acronym.includes(obj.defaultFilter),
      container,
      groupRadioName;

    groupRadioName = 'leaflet-exclusive-group-layer-' + obj.group.id;
    input = this._createRadioElement(groupRadioName, checked);

    input.ctrlId = obj.ctrlId;
    input.groupID = obj.group.id;
    L.DomEvent.on(input, 'click', this._onInputClick, this);

    var name = document.createElement('span');
    name.innerHTML = ' ' + obj.name;

    label.appendChild(input);
    label.appendChild(name);

    if (obj.overlay) {
      container = this._overlaysList;

      var groupContainer = this._domGroups[obj.group.id];

      // Create the group container if it doesn't exist
      if (!groupContainer) {
        groupContainer = document.createElement('div');
        groupContainer.className = 'leaflet-control-layers-group';
        groupContainer.id = 'leaflet-control-layers-group-' + obj.group.id;
        if( obj.group.name=="UNIDADE TEMPORAL")
          groupContainer.style="display:none;";

        var groupLabel = document.createElement('label');
        groupLabel.className = 'leaflet-control-layers-group-label';

        var groupName = document.createElement('span');
        groupName.className = 'leaflet-control-layers-group-name';
        groupName.innerHTML = obj.group.name;
        groupLabel.appendChild(groupName);

        groupContainer.appendChild(groupLabel);
        container.appendChild(groupContainer);

        this._domGroups[obj.group.id] = groupContainer;
      }

      container = groupContainer;
    } else {
      container = this._baseLayersList;
    }

    container.appendChild(label);

    return label;
  },

  _onInputClick: function (e) {
    let obj = this._getControlById(e.target.ctrlId);
    // dispache event to update layers using selected filters
    this._map.fire('changectrl', obj);
  },

  _expand: function () {
    L.DomUtil.addClass(this._container, 'leaflet-control-layers-expanded');
    L.DomUtil.addClass(this._form, 'leaflet-control-layers-scrollbar');
    this._form.style.height='auto';
  },

  _onWindowResize: function () {
    // permits to have a scrollbar if overlays heighter than the map. 
    var acceptableHeight = $('#map').height() - (this._container.offsetTop * 2);
    if (this._form.scrollHeight>acceptableHeight) {
      this._form.style.height = acceptableHeight + 'px';
    }else{
      this._form.style.height='auto';
    }
  },

  _collapse: function () {
    this._container.className = this._container.className.replace(' leaflet-control-layers-expanded', '');
  },

  _indexOf: function (arr, obj) {
    for (var i = 0, j = arr.length; i < j; i++) {
      if (arr[i] === obj) {
        return i;
      }
    }
    return -1;
  }
});

L.control.groupedLayers = function (controlGroups, options) {
  return new L.Control.GroupedLayers(controlGroups, options);
};
