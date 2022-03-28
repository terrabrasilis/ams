var ams = ams || {};

ams.Auth = {
	/**
	 * Default GeoServer workspace for anonymous users.
	 * The GeoServer workspace name for authenticated users is "ams_auth" by convention.
	 */
	gsWorkspace:'ams',
	/**
	 * Default is no suffix. To authenticate the suffix is "_auth"
	 */
	gsAuthSuffix:'',

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
	},

  /**
   * Check if the user is authenticated.
   */
  isAuthenticated: function() {
    return ( (typeof Authentication!="undefined" && Authentication.hasToken())?(true):(false) );
  },

  getAuthSuffix: function() {
    return this.gsAuthSuffix;
  },

  /**
   * Workspace always use the suffix. For anonymous users, the suffix is empty.
   * Looking for homologation URL or development env. If found forces the amsh (homologation workspace)
   * Must have a homologation workspace on the geoserver
   */
  getWorkspace: function() {
	if(window.location.pathname.includes("homologation") || window.location.hostname=='127.0.0.1'){
		this.gsWorkspace='amsh';
	}
    return this.gsWorkspace+this.gsAuthSuffix;
  },

  setWorkspace: function(workspace) {
    this.gsWorkspace=workspace;
  }
};