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

  let setMapHeight=()=>{
    $('#map').height(window.innerHeight-$('footer.footer').height()-$('#content').height());
  };
    
  $("#sidebar").mCustomScrollbar({
      theme: "minimal"
  });

  $('#sidebarCollapse, #prepare_print').on('click', toggleSideBar);

  // close side bar by default
  toggleSideBar();
  // set map div to available height
  setMapHeight();
  // start webapp based on definitions inside index.html
  startApp();

  /** display app version on footer bar */
  let versionDiv = $('#version');
  if(versionDiv.length>0){
    // TODO: enable this code if a file with tag version is present
    $.getJSON('static/PROJECT_VERSION', function(data) {
        let version = data.version;
        versionDiv.append('<a href="https://github.com/terrabrasilis/ams/releases/tag/'+version+'" target="_blank" title="Veja este release no GitHub">'+version+'</a>');
        if(window.location.pathname.includes("homologation")){
          $('#header-panel').append("<span style='font-size:18px;font-weight:600;color:#ffff00;'> (Versão de homologação)</span>")
        }
    });
  }

  /** init authentication component */
  let Lang={language:"pt-br", change:(l)=>{alert("Na fila de implementação.");}};
  Authentication.init(Lang.language, function(){
      console.log("The authentication component has been loaded");
  });

  /** config google analytics */
  window.dataLayer = window.dataLayer || [];
  function gtag() { dataLayer.push(arguments); }
  gtag('js', new Date());
  gtag('config', 'G-VF4139FH8F');

  var tid=null;
  window.onresize=()=>{
    if(tid) window.clearTimeout(tid);
    tid=window.setTimeout(
      ()=>{
        tid=null;
        setMapHeight();
        ams.App._onWindowResize();
      },200
    );
  };
});



      