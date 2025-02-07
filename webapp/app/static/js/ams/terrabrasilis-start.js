$(document).ready(function () {

  let toggleSideBar=()=> {
    $('#sidebar, #content').toggleClass('active');
    $('.collapse.in').toggleClass('in');
    $('a[aria-expanded=true]').attr('aria-expanded', 'false');
    // no sense because when side bar has class active the return is false
    if($('#sidebar').hasClass('active')){// if open
        $('#panel_container').addClass('full-width');
    }else{//if close
        $('#panel_container').removeClass('full-width');
    }
  };
    
  $("#sidebar").mCustomScrollbar({
      theme: "minimal"
  });

  $('#sidebarCollapse, #prepare_print').on('click', toggleSideBar);

  // close side bar by default
  toggleSideBar();
  
  /** display app version on footer bar */
  let versionDiv = $('#version');
  if(versionDiv.length>0){
    if(localStorage.getItem('ams.appVersion')!==null && appVersion!=localStorage.getItem('ams.appVersion')){
      // if app version changes, clear the local storage to force reload configs
      ams.Utils.resetlocalStorage();
    }
    localStorage.setItem('ams.appVersion', appVersion );
    versionDiv.append('<a href="https://github.com/terrabrasilis/ams/releases/tag/'+appVersion+'" target="_blank" title="Veja este release no GitHub">'+appVersion+'</a>');
    if(ams.Utils.isHomologationEnvironment()){
        $('#header-panel-info').append(" (Versão de homologação)");
    }
  }

  /** Translation component mock, used to start the authentication component */
  let Lang={language:"pt-br", change:(l)=>{alert("Na fila de implementação.");}};
  /**
   * When starting the authentication component, register the restartApp callback
   * to restart the webapp based on the definitions in index.html and the status
   * of the authentication chain.
   */
  if(typeof Authentication != 'undefined')
  {
    let authenticationClientId = null
    let authenticationResourceRole = null;
    if(defaultConfig.general.authenticationClientId)
    {
      authenticationClientId = defaultConfig.general.authenticationClientId;
    }

    if(defaultConfig.general.authenticationResourceRole)
    {
      authenticationResourceRole = defaultConfig.general.authenticationResourceRole;
    }
    
    Authentication.init(Lang.language, ams.Utils.restartApp, "", authenticationClientId, authenticationResourceRole);
  }  

  /** Launch the app when loading the page for the first time */
  if (ams.Utils.getServerConfigParam('reset_local_storage') === "True") {
      ams.Utils.resetlocalStorage();
  }

  ams.Utils.startApp();

  /** config google analytics */
  window.dataLayer = window.dataLayer || [];
  function gtag() { dataLayer.push(arguments); }
  gtag('js', new Date());
  gtag('config', 'G-VF4139FH8F');

  /** Defines what to do for the window resize event */
  window.onresize=ams.Utils.onWindowResize;
});
