$(document).ready(function () {
    
  $("#sidebar").mCustomScrollbar({
      theme: "minimal"
  });

  $('#sidebarCollapse, #prepare_print').on('click', function () {
      $('#sidebar, #content').toggleClass('active');
      $('.collapse.in').toggleClass('in');
      $('a[aria-expanded=true]').attr('aria-expanded', 'false');
      // no sense because when side bar has class active the return is false
      if($('#sidebar').hasClass('active')){// if open
          $('#panel_container').addClass('full-width');
      }else{//if close
          $('#panel_container').removeClass('full-width');
      }
      // TODO: if the application context needs to be resized, call the resize function here
  });

  /** display app version on footer bar */
  let versionDiv = $('#version');
  if(versionDiv.length>0){
    versionDiv.append('ver: 1.0.0');
    // TODO: enable this code if a file with tag version is present
    $.getJSON('PROJECT_VERSION', function(data) {
        let version = data.version;
        versionDiv.append('ver: '+version);
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
});



      