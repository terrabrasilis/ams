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
  let appVersion = '1.0.0';
  if(versionDiv.length>0){
    // TODO: enable this code if a file with tag version is present
    $.getJSON('static/PROJECT_VERSION', function(data) {
        appVersion = data.version;
        ams.Config.appVersion=appVersion;
        localStorage.setItem('ams.config.appversion', appVersion );
        versionDiv.append('<a href="https://github.com/terrabrasilis/ams/releases/tag/'+appVersion+'" target="_blank" title="Veja este release no GitHub">'+appVersion+'</a>');
        if(ams.Utils.isHomologationEnvironment()){
          $('#header-panel').append("<span style='font-size:18px;font-weight:600;color:#ffff00;'> (Versão de homologação)</span>");
        }
    });
  }

  /** Translation component mock, used to start the authentication component */
  let Lang={language:"pt-br", change:(l)=>{alert("Na fila de implementação.");}};
  /**
   * When starting the authentication component, register the restartApp callback
   * to restart the webapp based on the definitions in index.html and the status
   * of the authentication chain.
   */
  if(typeof Authentication != 'undefined')
    if(ams.Utils.isHomologationEnvironment()) Authentication.init(Lang.language, ams.Utils.restartApp, "http://terrabrasilis.dpi.inpe.br/oauth-api/");
    else Authentication.init(Lang.language, ams.Utils.restartApp);

  /** Launch the app when loading the page for the first time */
  ams.Utils.startApp();

  /** config google analytics */
  window.dataLayer = window.dataLayer || [];
  function gtag() { dataLayer.push(arguments); }
  gtag('js', new Date());
  gtag('config', 'G-VF4139FH8F');

  /** Defines what to do for the window resize event */
  window.onresize=ams.Utils.onWindowResize;
});