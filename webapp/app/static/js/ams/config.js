var ams = ams || {};
ams.BiomeConfig={};
ams.defaultBiome="Amazônia";

var defaultConfig = {
  terrabrasilisURL:"http://terrabrasilis.dpi.inpe.br",
  DETERMetadataURL: "/geonetwork/srv/eng/catalog.search#/metadata/f9b7e1d3-0d4e-4cb1-b3cf-c2b8906126be",
  AFMetadataURL: "/geonetwork/srv/eng/catalog.search#/metadata/c4b6504f-5d54-4b61-a745-4123fae873ec",
  spatialUnitLayers:[],// populated on App load: ams.App.run(...)
  floatDecimals: 2,// change this number to change the number of decimals to float numbers
  propertyName: {
    deter:"area",// can be "area", if reference layer is DETER
    af:"counts", // or "counts", if reference layer is AF - Active Fire (Focos de Queimadas)
    rk:"counts" // and "counts" to risk too, because risk is trated as points as Active Fire
  },
  risk:{
  },
  general:{
    area:{
      changeunit: "auto", // used to automatically change the area unit between km² and ha when the threshold changes
      threshold: 2 // if the absolute area value is less than threshold, the unit will be changed to ha
    },
    oauthAPIProxyURI: "/oauth-api/proxy?url=",
  },
  subset: {
      defaultMunicipality: 'Matopiba',
      defaultBiome: 'Cerrado',
      defaultFilters: {
          indicator: 'DS', // can be group's name of DETER classnames, 'DS', 'DG', 'CS' and 'MN', or 'AF' to Queimadas or 'RK' to risk
          spatialUnit: 'cs_150km',
          temporalUnit: '7d',
          diffClassify: 'onPeriod', // can be 'onPeriod' or 'periodDiff'
          priorityLimit: 10
      },
  }
};

ams.BiomeConfig["Amazônia"] = {
  defaultWorkspace: 'ams',
  defaultLayers:{
    biomeBorder:"prodes-amazon-nb:amazon_biome_border",// Layer name of Amazon biome border from TerraBrasilis service ( The workspace is fixed)
    deter:"deter-ams", // The layer name of DETER alerts from TerraBrasilis service. The workspace is dinamic and based on authentication state
    activeFire:"active-fire", // The layer name of Focos de Queimadas from TerraBrasilis service. The workspace is dinamic and based on authentication state
    ibamaRisk: "risk-ibama-weekly-data", // The layer name of weekly risk with the default prediction data of risk of deforestation from IBAMA.
    lastDate: "last_date" // The layer name to get the last update date of available data. The workspace is dinamic and based on authentication state
  },
  defaultFilters: {
    indicator: 'DS',// can be group's name of DETER classnames, 'DS', 'DG', 'CS' and 'MN', or 'AF' to Queimadas or 'RK' to risk
    spatialUnit: 'csAmz_150km',
    temporalUnit: '7d',
    diffClassify: 'onPeriod',// can be 'onPeriod' or 'periodDiff'
    priorityLimit: 10
  },
  defaultRiskFilter:{
    // used to process counts, including points where the value is greater than this threshold
    threshold: parseFloat(ams.Utils.getServerConfigParam('risk_threshold')),
    expirationRisk: 7 // The number of days to set the risk forecast due date.
  }
};

ams.BiomeConfig["Cerrado"] = {
  defaultWorkspace: 'cer',
  defaultLayers:{
    biomeBorder:"prodes-cerrado-nb:biome_border",// Layer name of Cerrado biome border from TerraBrasilis service. The workspace is fixed
    deter:"deter-ams", // The layer name of DETER alerts from TerraBrasilis service. The workspace is dinamic and based on authentication state
    activeFire:"active-fire", // The layer name of Focos de Queimadas from TerraBrasilis service. The workspace is dinamic and based on authentication state
    lastDate: "last_date" // The layer name to get the last update date of available data. The workspace is dinamic and based on authentication state
  },
  defaultFilters: {
    indicator: 'DS',// can be group's name of DETER classname 'DS' or 'AF' to Queimadas
    spatialUnit: 'csCer_150km',
    temporalUnit: '7d',
    diffClassify: 'onPeriod',// can be 'onPeriod' or 'periodDiff'
    priorityLimit: 10
  },
  defaultRiskFilter: {
    threshold: 0,
    expirationRisk: 0
  }
};

ams.BiomeConfig["Cerrado"] = {...ams.BiomeConfig["Cerrado"], ...defaultConfig};
ams.BiomeConfig["Amazônia"] = {...ams.BiomeConfig["Amazônia"], ...defaultConfig};
