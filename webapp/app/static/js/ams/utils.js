var ams = ams || {};

ams.Utils = {
  tid:null,

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

  /**
   * Used when autentication changes
   */
  restartApp: function(){

    /** 
     * TODO: Try remove an error "request is too large" when many data is appended into query string parameter
     * To authenticated users we need of access_token as a query string parameter in any requests to GeoServer
     */
    Authentication.eraseCookie(Authentication.tokenKey);

    var mapDiv=$('#map');
    if(mapDiv) {
      mapDiv.remove();
      $('#panel_container').append("<div id='map'>");
    }
    // set map div to available height
    ams.Utils.setMapHeight();
    startApp();
  },

  /**
   * Used to format a number to display in web view
   * This function uses the configuration value defined in Config.js to set the number of decimals (see: floatDecimals)
   * @param {number} n, the input number 
   */
  numberFormat: function(n){
    let sp=n.split('.');// determine if the number is floating by the existing point
    return ( (sp.length==2)?(parseFloat(n).toFixed(ams.Config.floatDecimals)):(parseInt(n)) );
  }
};