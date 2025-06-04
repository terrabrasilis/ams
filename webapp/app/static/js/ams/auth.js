var ams = ams || {};

ams.Auth = {
	/**
	 * Default GeoServer workspace for anonymous users loaded from server on app start.
	 * The GeoServer workspace name for authenticated users is concat with "_auth" by convention.
	 */
	gsWorkspace:null,
	/**
	 * Default is no suffix. To authenticate the suffix is "_auth"
	 */
	gsAuthSuffix:'',
	/**
	 * Default is no suffix. To homologation the suffix is "h"
	 */
	gsHomologationSuffix:'',

	/**
	 * Evaluates user authentication status and sets appropriate suffix
	 * 
	 * When starting the application or after user login, changes the default suffix
	 * to the suffix suitable for authenticated users.
	 * 
	 * The GeoServer workspace name for AMS or the layer name for Official DETER
	 * for authenticated users uses "_auth" by convention.
	 */
	evaluate: function() {
	    this.gsAuthSuffix=( (this.isAuthenticated())?("_auth"):("") );
	    // set the appropriate workspace name if it is homologation environment
	    this.gsHomologationSuffix=( (ams.Utils.isHomologationEnvironment())?('h'):('') );
	},

  /**
   * Check if the user is authenticated.
   */
  isAuthenticated: function () {
	return ( (typeof Authentication!="undefined" && Authentication.hasToken())?(true):(false) );
  },

  getAuthSuffix: function() {
      return this.gsAuthSuffix;
  },

  getOAuthProxyUrl: function(url)
  {
	return Authentication.getOAuthProxyUrl(url, AuthenticationService.getOAuthClientId(), AuthenticationService.getOAuthResouceRole());
  },

  /**
   * Workspace always use the suffix. For anonymous users, the suffix is empty.
   * Looking for homologation URL or development env. If found concat the "h" to current workspace (homologation workspace)
   * Must have a homologation workspace on the geoserver
   */
  getWorkspace: function() {
      if(!this.gsWorkspace){
	  this.gsWorkspace=ams.Config.defaultWorkspace;
      }
      return this.gsWorkspace+this.gsHomologationSuffix+this.gsAuthSuffix;
  },

  resetWorkspace: function(){
      this.gsWorkspace=null;
  }
};
