var ams = ams || {};

ams.Utils = {
  tid:null,

  isHomologationEnvironment: function(){
    return  window.location.pathname.includes("homologation") || window.location.hostname=='127.0.0.1';
  },

  setMapHeight: function(){
    $('#map').height(window.innerHeight-$('footer.footer').height()-$('#content').height());
  },

  onWindowResize: function(){
    if(ams.Utils.tid) window.clearTimeout(ams.Utils.tid);
    ams.Utils.tid=window.setTimeout(
      ()=>{
        ams.Utils.tid=null;
        ams.Utils.setMapHeight();
        ams.App._onWindowResize();
      },200
    );
  },

  getServerConfigParam: function(param) {
      return $('meta[name="' + param + '"]').attr('content');
  },

  getGeneralConfig: function () {
    let generalConfig = localStorage.getItem('ams.session.generalConfig');

    if (generalConfig !== null) {
      return JSON.parse(generalConfig);
    }

    return undefined;
  },

  startApp: function(generalConfig){
    if (generalConfig === undefined) {
      ams.Utils.updateMap();
      return;
    }

    // evaluate the user area_profile on start app
    ams.Auth.evaluate();

    // set map div to available height
    ams.Utils.setMapHeight();

    // config
    var biome = generalConfig.appBiome.split(",")[0];

    ams.Config = ams.BiomeConfig[biome];

    ams.Config.allBiomes = JSON.parse(generalConfig.biomes.replace(/'/g,"\""));
    ams.Config.allMunicipalitiesGroup = JSON.parse(generalConfig.municipalities_group.replace(/'/g,"\""));
    ams.Config.landUses = JSON.parse(generalConfig.land_uses.replace(/'/g,"\""));

    ams.Config.biome = generalConfig.appBiome;
    ams.Config.appSelectedSubset = generalConfig.selected_subset;
    ams.Config.appSelectedBiomes = JSON.parse(generalConfig.selected_biomes.replace(/'/g,"\""));
    ams.Config.appSelectedMunicipalitiesGroup = generalConfig.selected_municipalities_group;
    ams.Config.publishDate = generalConfig.publish_date;
    ams.Config.bbox = JSON.parse(generalConfig.bbox);

    ams.Config.appSelectedGeocodes = JSON.parse(generalConfig.selected_geocodes);
    ams.Config.appAllMunicipalities = JSON.parse(generalConfig.all_municipalities.replace(/'/g,"\""));

    ams.Config.appMunicipalityPanelMode = JSON.parse(generalConfig.municipality_panel_mode);
    ams.Config.appSelectedMunicipality = generalConfig.selected_municipality;

    ams.Config.startDate = generalConfig.start_date;
    ams.Config.endDate = generalConfig.end_date;
    ams.Config.tempUnit = generalConfig.temp_unit;

    if (generalConfig.classname) {
      ams.Config.defaultFilters.indicator	= generalConfig.classname;
    }

    var spatialUnits = JSON.parse(generalConfig.spatial_units_info_for_subset.replace(/'/g,"\""));
    var spatialUnitsSubset = new ams.Map.SpatialUnits(spatialUnits, spatialUnits[0]["dataname"]);

    var appClassGroups = new ams.Map.AppClassGroups(
      JSON.parse(generalConfig.deter_class_groups.replace(/'/g,"\""))
    );

    var geoserverUrl = generalConfig.geoserver_url;

    try {
      ams.App.run(geoserverUrl, spatialUnitsSubset, appClassGroups);

    } catch (error) {
      console.log(error);
      // if any error occurs, clear the local storage to try again
      ams.Utils.resetlocalStorage();
    }

  },

  /**
   * Used when autentication changes
   */
  restartApp: function(resetMap=false) {
    if (!resetMap && ams.Auth.isAuthenticated()) {
      return;
    }

    Authentication.eraseCookie(Authentication.tokenKey);
      
    var mapDiv=$('#map');
    if(mapDiv) {
      mapDiv.remove();
      $('#panel_container').append("<div id='map'>");
    }

    ams.Utils.setMapHeight();
    ams.Utils.startApp();
  },

   /**
    * Used when selected biome changes
    */
    updateMap: function(
        selectedBiome,
        selectedSubset,
        selectedMunicipalitiesGroup,
        selectedGeocodes,
	      startDate,
        endDate,
	      tempUnit
    ) {

      if (selectedBiome === undefined) {
        selectedBiome = ams.defaultBiome;
      }

      if (selectedSubset === undefined) {
          selectedSubset = ams.defaultSubset;
      }

      if (selectedMunicipalitiesGroup === undefined) {
          selectedMunicipalitiesGroup = ams.defaultMunicipalitiesGroup;
      }

      if (selectedGeocodes === undefined) {
          selectedGeocodes = "";
      }

      var municipalityPanelMode = false,
        classname = "";      
      if (ams.Utils.getServerConfigParam('municipality-panel') !== undefined) {
          municipalityPanelMode = true;
          selectedBiome = "ALL";
          selectedSubset = "Municípios de Interesse";
          selectedMunicipalitiesGroup = "customizado";
          selectedGeocodes=ams.Utils.getServerConfigParam('geocode');
          startDate=ams.Utils.getServerConfigParam('start_date');
          endDate=ams.Utils.getServerConfigParam('end_date');
          tempUnit=ams.Utils.getServerConfigParam('temp_unit');
          classname=ams.Utils.getServerConfigParam('classname');
      }

      if (startDate === undefined) {
        startDate = "";
      }

      if (endDate === undefined) {
        endDate = "";
      }

      if (tempUnit === undefined) {
        tempUnit = "";
      }

      const loadConfig = new Promise((resolve, reject) => {

        /**
         * If we need read configurations from server by a selected biome.
         * @param {string} selectedBiome The name of selected biome.
         */
        async function getConfig(
            selectedBiome, selectedSubset, selectedMunicipalitiesGroup, selectedGeocodes, municipalityPanelMode
        ) {
          let response = await fetch(
              "biome/config?targetbiome=" + selectedBiome +
              "&subset=" + selectedSubset +
              "&municipalitiesGroup=" + selectedMunicipalitiesGroup +
              "&isAuthenticated=" + ams.Auth.isAuthenticated() +
              "&geocodes=" + selectedGeocodes +
              "&municipalityPanelMode=" + municipalityPanelMode +
	            "&startDate=" + ((startDate !== undefined)? startDate : "") +
              "&endDate=" + ((endDate !== undefined)? endDate : "") +
	            "&tempUnit=" + ((tempUnit !== undefined)? tempUnit : "") +
              "&classname=" + classname
          );

          if (response&&response.ok) {
            let generalConfig = await response.json();

            if (generalConfig.appBiome) {
              ams.Utils.startApp(generalConfig);

              resolve();

            } else {
              console.log("HTTP-Error: " + response.status + " on biome changes");
              $('.toast').toast('show');
              $('.toast-body').html("Encontrou um erro na solicitação ao servidor.");

              reject("HTTP-Error: " + response.status + " on biome changes");
            }
          } else {
            if (response) console.log("HTTP-Error: " + response.status + " on biome changes");

            $('.toast').toast('show');
            $('.toast-body').html("Encontrou um erro na solicitação ao servidor.");

            reject("HTTP-Error: " + response.status + " on biome changes");
          }
        };

        delete ams.Map.PopupControl._popupReference;
        ams.Map.PopupControl._infoBody=[];

        // reset map container
        let mapDiv=$('#map');
        if(mapDiv) {
          mapDiv.remove();
          $('#panel_container').append("<div id='map'>");
        }
        ams.Utils.setMapHeight();
        ams.Auth.resetWorkspace();
       
        getConfig(
          selectedBiome, selectedSubset, selectedMunicipalitiesGroup, selectedGeocodes, municipalityPanelMode
        );

      });// end of promise

      return loadConfig;
    },

  /**
   * Used to format a number to display in web view
   * This function uses the configuration value defined in Config.js to set the number of decimals (see: floatDecimals)
   * @param {number} n, the input number 
   */
  numberFormat: function(n){
    n=n+'';
    let sp=n.split('.');// determine if the number is floating by the existing point
    return ( (sp.length==2)?(parseFloat(n).toFixed(ams.Config.floatDecimals)):(parseInt(n)) );
  },

  /**
   * Reset all data on local storage
   */
  resetlocalStorage: function(){
    localStorage.clear();
  },

    /**
     * Assertion.
     */
    assert: function(condition, msg) {
        if (!condition) {
            throw new Error(msg || "assertion error");
        }
    },

};
