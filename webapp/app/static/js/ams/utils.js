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
  }
};