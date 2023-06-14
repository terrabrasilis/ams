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
    this._landUseItens = L.DomUtil.create('div', 'landuse-itens');

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
    this._landUseItens.innerHTML = '';
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

    let dctrl=this._getDownloadControlDOM();
    this._overlaysList.appendChild(dctrl);

    this._separator.style.display = overlaysPresent && baseLayersPresent ? '' : 'none';
  },

  // IE7 bugs out if you create a radio dynamically, so you have to do it this hacky way (see http://bit.ly/PqYLBe)
  _createInputElement: function (name, type, checked) {
    var inputHtml = '<input type="'+type+'" class="leaflet-control-layers-selector" name="' + name + '"';
    if (checked) {
      inputHtml += ' checked="checked"';
    }
    inputHtml += '/>';

    var inputFragment = document.createElement('div');
    inputFragment.innerHTML = inputHtml;

    return inputFragment.firstChild;
  },

  _createProfileBiomeButton: function(biome) {

    let biomeId=ams.BiomeConfig[biome].defaultWorkspace;

    let bt='<button title="Visualize o perfil para todo o bioma."'
    +' class="btn btn-primary-p profile-bt"'
    +' id="profile-'+biomeId+'-button">'
    +'<i class="material-icons profile-bt-icon">leaderboard</i>Perfil</button>';

    var btFragment = document.createElement('div');
    btFragment.innerHTML = bt;

    return btFragment;
  },

  _createLandUseButton: function() {

    let bt='<button title=\'Desmarcar ou marcar todas as categorias.\''
    +' class="btn btn-primary-p landuse-bt lu-all-bt"'
    +' id="all-categories-button">'
    +'<i class="material-icons profile-bt-icon">check_box</i>Todas</button>'
    + '<button title=\'Aplica filtro com as categorias fundiárias selecionadas.\''
    +' class="btn btn-primary-p landuse-bt lu-ft-bt"'
    +' id="landuse-categories-button">'
    +'<i class="material-icons profile-bt-icon">filter_alt</i>Aplicar</button>';

    var btFragment = document.createElement('div');
    btFragment.className = "landuse";
    btFragment.innerHTML = bt;

    return btFragment;
  },

  _addItem: function (obj) {
    // for initial state of checked control, use the ams.Config.defaultFilters defines...

    var label = document.createElement('label'),
      input,
      checked = (obj.group.name=="CATEGORIA FUNDIÁRIA")?(obj.defaultFilter.includes(obj.acronym)):(obj.acronym.includes(obj.defaultFilter)),
      container,
      groupRadioName,
      profileBt=null,
      type=(obj.group.name=="CATEGORIA FUNDIÁRIA")?('checkbox'):('radio');

    groupRadioName = 'leaflet-exclusive-group-layer-' + obj.group.id;
    input = this._createInputElement(groupRadioName, type, checked);

    input.ctrlId = obj.ctrlId;
    input.groupID = obj.group.id;
    L.DomEvent.on(input, 'click', this._onInputClick, this);

    var name = document.createElement('span');
    name.innerHTML = ' ' + obj.name;

    if(obj.group.name=="BIOMA"){
      let divbiome = document.createElement('div');
      divbiome.appendChild(input);
      divbiome.appendChild(name);
      label.appendChild(divbiome);
      label.className = 'leaflet-biome-control-item';

      // adding profile biome button
      if(checked){
        profileBt = this._createProfileBiomeButton(obj.name);
        label.appendChild(profileBt);
      }
    }
    else if (obj.group.name == "INDICADOR") {
      label.appendChild(input);
      label.appendChild(name);
    
      L.DomEvent.on(input, 'click', function() {
        // Risk radio button is selected?
        if (obj.name.toLowerCase().includes('risco') && input.checked) {
          // Remove period control
		      ams.PeriodHandler.remove(this._map);
          // Adding risk control 
		      ams.RiskThresholdHandler.init(this._map);
        } else {
          // Adding period control over map
		      ams.PeriodHandler.init(this._map);
          // Remove risk control 
		      ams.RiskThresholdHandler.remove(this._map);
        }
      }, this);
    }else{
      label.appendChild(input);
      label.appendChild(name);
    }

    if (obj.overlay) {
      container = this._overlaysList;

      var groupContainer = this._domGroups[obj.group.id];

      // Create the group container if it doesn't exist
      if (!groupContainer) {
        groupContainer = document.createElement('div');
        groupContainer.className = 'leaflet-control-layers-group';
        groupContainer.id = 'leaflet-control-layers-group-' + obj.group.id;
        groupContainer.title = this._getTitleByGroup(obj.group.name);
        if(obj.group.name=="UNIDADE TEMPORAL")
          groupContainer.style="display:none;";
        if(obj.group.name=="CATEGORIA FUNDIÁRIA")
          groupContainer.className = 'leaflet-control-layers-group lclg-landuse';

        var groupLabel = document.createElement('label');
        groupLabel.className = 'leaflet-control-layers-group-label';
        if(obj.group.name=="CATEGORIA FUNDIÁRIA")
          groupLabel.style="border-top-right-radius: unset; background-color: #dae9c5;";

        var groupName = document.createElement('span');
        groupName.className = 'leaflet-control-layers-group-name';
        if(obj.group.name=="CATEGORIA FUNDIÁRIA")
          groupName.style = "color: #3e3e3e;";
        groupName.innerHTML = obj.group.name;
        groupLabel.appendChild(groupName);
        groupContainer.appendChild(groupLabel);

        if(obj.group.name=="CATEGORIA FUNDIÁRIA"){
          var groupIcon = document.createElement('i');
          groupIcon.className = 'material-icons iconlanduse-updown';
          groupIcon.innerText = 'arrow_drop_down';
          groupContainer.appendChild(groupIcon);
        }

        container.appendChild(groupContainer);

        if(obj.group.name=="UNIDADE ESPACIAL"){
          let pctrl=this._getPriorityControlDOM();
          container.appendChild(pctrl);
        }

        if(obj.group.name=="CATEGORIA FUNDIÁRIA"){
          this._landUseItens.id = 'landuse-itens';
          this._landUseItens.title = this._getTitleByGroup(obj.group.name+'_info');
          let landUseBt = this._createLandUseButton();
          this._landUseItens.appendChild(landUseBt);
          let innerDiv = document.createElement('div');
          innerDiv.id = "ckb-itens";
          this._landUseItens.appendChild(innerDiv);
          container.appendChild(this._landUseItens);
          this._landUseItens=innerDiv;
        }

        this._domGroups[obj.group.id] = groupContainer;
      }

      container = groupContainer;
    } else {
      container = this._baseLayersList;
    }
    if(obj.group.name=="CATEGORIA FUNDIÁRIA") this._landUseItens.appendChild(label);
    else container.appendChild(label);

    return label;
  },

  _getTitleByGroup: function(grpName) {
    let title='';
    switch (grpName) {
      case "BIOMA":
        title='Alterna entre as bases de dados dos biomas disponíveis.';
        break;
      case "INDICADOR":
        title='Aplica um filtro com base nas classes dos dados do DETER e focos do Programa Queimadas, sendo:\n';
        for (let index = 0; index < ams.App._appClassGroups.groups.length; index++) {
          const group = ams.App._appClassGroups.groups[index];
          title+=' - '+group.name+': '+group.classes.join(', ')+';\n';
        }
        break;
      case "UNIDADE ESPACIAL":
        title='Alterna entre as unidades espaciais disponíveis.';
        break;
      case "CATEGORIA FUNDIÁRIA":
        title='Permite selecionar categorias fundiárias para restringir a apresentação dos dados.';
        break;
      case "CATEGORIA FUNDIÁRIA_info":
        title='Descrição das categorias fundiárias.\n\n'+
        'TI: Terras Indígenas;\n'+
        'UC: Unidades de Conservação;\n'+
        'Assentamentos: Projetos de assentamentos de todos os tipos;\n'+
        'APA: Área de Proteção Ambiental;\n'+
        'CAR: Cadastro Ambiental Rural;\n'+
        'FPND: Florestas Públicas Não Destinadas;\n'+
        'Indefinida: Todas as demais áreas';
        break;
      case "CLASSIFICAÇÃO DO MAPA":
        title='A opção "No Período" destaca as unidades espaciais por intervalos de valor, com destaque para os maiores valores absolutos.\n\n';
        title+='A opção "Diferença Período Anterior" destaca as unidades espaciais por intervalos de valor, considerando a diferença de valor entre o período selecionado e o período anterior.\n';
        title+=' - Destaque em tons de vermelho indicam aumento do valor no período corrente em relação ao período anterior.\n';
        title+=' - Destaque em tons de azul indicam diminuição do valor no período corrente em relação ao período anterior.\n';
        break;
      default:
        break;
    }
    return title;
  },

   /**
   * Make the priority control DOM fragment
   */
  _getPriorityControlDOM: function() {
    let fctrl = document.createElement('div');
    let title = 'title="Altera o número de unidades espaciais consideradas na priorização de exibição do mapa.\n';
    title = title + 'Irá destacar, com borda vermelha, as unidades espaciais com maior valor agregado para o período." ';
    
    fctrl.innerHTML='<div class="leaflet-control-layers-group" id="prioritization-control-layers-group">'
    + '<label class="leaflet-control-layers-group-name" '+title+'>'
    + '<span class="leaflet-control-layers-group-name">Prioriza&#231;&#227;o </span>'
    + '<input type="number" id="prioritization-input" min="1" style="width:45px" '
    + title
    + 'value=' + ams.App._priorViewParams.limit + ' />'
    + '<button class="btn btn-primary-p" id="prioritization-button" style="margin-left: 10px;"> Ok </button>'
    + '</label></div>';
    return fctrl.firstChild;
  },

   /**
   * Make the download control DOM fragment
   */
  _getDownloadControlDOM: function() {
    let fctrl = document.createElement('div');
    let title = 'title="O arquivo inclui dados filtrados por: BIOMA, INDICADOR e PERÍODO.\n';
    title = title + ' - CSV: inclui apenas as unidades espaciais priorizadas;\n';
    title = title + ' - Shapefile: inclui todas as unidades espaciais;" ';
    fctrl.innerHTML='<div class="leaflet-control-layers-group" id="shapezip-control-layers-group">'
    + '<label class="leaflet-control-layers-group-label">'
    + '<span class="leaflet-control-layers-group-name">DOWNLOAD</span></label>'
    + '<label class="leaflet-control-layers-group-name" '+title+'>'
    + '<span style="white-space: pre-wrap;">'
    + 'Baixar arquivo da unidade<br>espacial selecionada.</span></label>'
    + '<label class="leaflet-control-layers-group-name btn-download">'
    + '<button class="btn btn-primary-p btn-success" id="csv-download-button"> CSV </button>'
    + '&nbsp;&nbsp;'
    + '<button class="btn btn-primary-p btn-success" id="shapezip-download-button"> Shapefile </button>'
    + '</label>'
    + '</div>';
    return fctrl.firstChild;
  },

  _onInputClick: function (e) {
    let obj = this._getControlById(e.target.ctrlId);
    obj["inputtype"]=e.target.type;
    obj["checked"]=e.target.checked;
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
