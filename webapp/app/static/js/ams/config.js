var ams = ams || {};
ams.BiomeConfig={};

ams.defaultSubset="Bioma";
ams.defaultMunicipalitiesGroup="customizado";
ams.defaultBiome="Amazônia";

var defaultConfig = {
  terrabrasilisURL:"http://terrabrasilis.dpi.inpe.br",
  DETERMetadataURL: "/geonetwork/srv/eng/catalog.search#/metadata/f2153c4a-915b-48a6-8658-963bdce7366c",
  AFMetadataURL: "/geonetwork/srv/eng/catalog.search#/metadata/c4b6504f-5d54-4b61-a745-4123fae873ec",
  spatialUnitLayers:[],// populated on App load: ams.App.run(...)
  floatDecimals: 2,// change this number to change the number of decimals to float numbers
  propertyName: {
    deter: "area",// can be "area", if reference layer is DETER
    af: "counts", // or "counts", if reference layer is AF - Active Fire (Focos de Queimadas)
    rk: "counts", // and "counts" to risk too, because risk is trated as points as Active Fire,
    ri: "score"
  },
  risk:{
  },
  general:{
    area:{
      changeunit: "auto", // used to automatically change the area unit between km² and ha when the threshold changes
      threshold: 2 // if the absolute area value is less than threshold, the unit will be changed to ha
    },
    authenticationClientId: "terrabrasilis-apps",
    authenticationResourceRole: "terrabrasilis-user"   
  }
};

// default definitions
const defaultLayers = {
  biomeBorder:"biome_border",
  municipalitiesBorder:"municipalities_border",
  // the layer name of DETER alerts from TerraBrasilis service
  deter: "deter-ams",
  // the layer name of Focos de Queimadas from TerraBrasilis service
  activeFire:"active-fire",
  // the layer name to get the last update date of available data
  lastDate: "last_date"
};

const defaultFilters = {
  spatialUnit: 'cs_150km',
  temporalUnit: '7d',
  // can be 'onPeriod' or 'periodDiff'
  diffClassify: 'onPeriod',
  priorityLimit: 10
};

const defaultRiskFilter = {
  threshold: 0,
  expirationRisk: 0
};

const defaultWorkspace = ams.Utils.isHomologationEnvironment()? "ams1" : "ams2";

// configuration by biome
ams.BiomeConfig["Amazônia"] = {
  defaultWorkspace: defaultWorkspace,
  defaultLayers: {
    ...defaultLayers,
    // the layer name of weekly risk with the default prediction data of risk of deforestation from IBAMA.
    ibamaRisk: "risk-ibama-weekly-data",
    // the layer name of risk from INPE.
    inpeRisk: "risk-inpe-data",
  },
  defaultFilters: {
    ...defaultFilters,
    // can be group's name of DETER classnames, 'DS', 'DG', 'CS' and 'MN', or 'AF' to Queimadas, or 'RK' to IBAMA risk or 'RI' to INPE risk
    indicator: 'DS',
  },
  defaultRiskFilter:{
    // used to process counts, including points where the value is greater than this threshold
    source: ams.Utils.getServerConfigParam('risk_inpe').toLowerCase() === "true"? "inpe" : "ibama",
    threshold: parseFloat(ams.Utils.getServerConfigParam('risk_threshold')),
    expirationRisk: 7, // The number of days to set the risk forecast due date.
    scaleFactor: parseFloat(ams.Utils.getServerConfigParam('risk_scale_factor'))
  }
};

const activeFiresLayerConfig = {
  defaultWorkspace: defaultWorkspace,
  defaultLayers: defaultLayers,
  defaultFilters: {
    ...defaultFilters,
    indicator: 'AF',
  },
  defaultRiskFilter: defaultRiskFilter
};

ams.BiomeConfig["Amazônia"] = {...ams.BiomeConfig["Amazônia"], ...defaultConfig};
ams.BiomeConfig["Cerrado"] = {...activeFiresLayerConfig, ...defaultConfig};
ams.BiomeConfig["Pantanal"] = {...activeFiresLayerConfig, ...defaultConfig};
ams.BiomeConfig["Caatinga"] = {...activeFiresLayerConfig, ...defaultConfig};
ams.BiomeConfig["Pampa"] = {...activeFiresLayerConfig, ...defaultConfig};
ams.BiomeConfig["Mata Atlântica"] = {...activeFiresLayerConfig, ...defaultConfig};
ams.BiomeConfig["ALL"] = {...ams.BiomeConfig["Amazônia"], ...defaultConfig};
