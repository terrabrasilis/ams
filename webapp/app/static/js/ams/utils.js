var ams = ams || {};

ams.Utils = {
  tid:null,

  isHomologationEnvironment: function(){
    return window.location.pathname.includes("homologation") || window.location.hostname=='127.0.0.1';
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

  startApp: function(generalConfig){

    if(typeof generalConfig=='undefined'){
      // use the previous selection or default biome (see config.js)
      let b=localStorage.getItem('ams.previous.biome.setting.selection');
      ams.Utils.biomeChanges( ((b!==null)?(b):(ams.defaultBiome)) );
    }else{
      // evaluate the user area_profile on start app
      ams.Auth.evaluate();
      // set map div to available height
      ams.Utils.setMapHeight();
      var sus = JSON.parse(generalConfig.spatial_units_info.replace(/'/g,"\""));
      ams.Config = ams.BiomeConfig[generalConfig.appBiome];
      ams.Config.biome=generalConfig.appBiome;
      ams.Config.landUses=JSON.parse(generalConfig.land_uses.replace(/'/g,"\""));
      var spatialUnits = new ams.Map.SpatialUnits(sus, ams.Config.defaultFilters.spatialUnit);
      var appClassGroups = new ams.Map.AppClassGroups(JSON.parse(generalConfig.deter_class_groups.replace(/'/g,"\"")));
      var geoserverUrl = generalConfig.geoserver_url;
      try {
        ams.App.run(geoserverUrl, spatialUnits, appClassGroups);
      } catch (error) {
        console.log(error);
        // if any error occurs, clear the local storage to try again
        ams.Utils.resetlocalStorage();
      }
    }
  },

  /**
   * Used when autentication changes
   */
  restartApp: function(){

    Authentication.eraseCookie(Authentication.tokenKey);

    var mapDiv=$('#map');
    if(mapDiv) {
      mapDiv.remove();
      $('#panel_container').append("<div id='map'>");
    }
    // set map div to available height
    ams.Utils.setMapHeight();
    ams.Utils.startApp();
  },

    /**
   * Used when selected biome changes
   */
    biomeChanges: function(selectedBiome){

      const loadConfig = new Promise((resolve, reject) => {

        /**
         * If we need read configurations from server by a selected biome.
         * @param {string} selectedBiome The name of selected biome.
         */
        async function getConfigByBiome( selectedBiome ) {
          let response = await fetch("biome/config?targetbiome=" + selectedBiome);
          if (response&&response.ok) {
            let generalConfig = await response.json();
            if (generalConfig.appBiome) {
              // write on local storage
              localStorage.setItem('ams.biome.config.'+selectedBiome, JSON.stringify(generalConfig));
              localStorage.setItem('ams.config.created.at', (new Date()).toISOString().split('T')[0] );
              ams.Utils.startApp(generalConfig);
              resolve();
            }else{
              console.log("HTTP-Error: " + response.status + " on biome changes");
              $('.toast').toast('show');
              $('.toast-body').html("Encontrou um erro na solicitação ao servidor.");
              reject("HTTP-Error: " + response.status + " on biome changes");
            }
          }else{
            if(response) console.log("HTTP-Error: " + response.status + " on biome changes");
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
        // set map div to available height
        ams.Utils.setMapHeight();
        //reset workspace
        ams.Auth.resetWorkspace();

        // Used to load from local storage
        if(localStorage.getItem('ams.biome.config.'+selectedBiome)!==null
            && localStorage.getItem('ams.config.created.at')!==null){
          
          // the local storage expiration date 
          let createdAt=new Date(localStorage.getItem('ams.config.created.at')+'T03:00:00.000Z');
          let nowDate=new Date((new Date()).toISOString().split('T')[0]+'T03:00:00.000Z');
          if(createdAt<nowDate){
            for (let p in ams.BiomeConfig) {
              if(ams.BiomeConfig.hasOwnProperty(p))
                localStorage.removeItem('ams.biome.config.'+p);
            }
            getConfigByBiome(selectedBiome);
          }else{
            let biomeConfiguration=JSON.parse(localStorage.getItem('ams.biome.config.'+selectedBiome));
            ams.Utils.startApp(biomeConfiguration);
            resolve();
          }
        }else{
          getConfigByBiome(selectedBiome);
        }

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
