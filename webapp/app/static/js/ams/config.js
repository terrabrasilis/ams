var ams = ams || {};
ams.BiomeConfig={};

ams.defaultSubset="Bioma";
ams.defaultMunicipalitiesGroup="customizado";
ams.defaultBiome="Amazônia";

var defaultConfig = {
  terrabrasilisURL:"http://terrabrasilis.dpi.inpe.br",
  DETERMetadataURL: "/geonetwork/srv/eng/catalog.search#/metadata/f2153c4a-915b-48a6-8658-963bdce7366c",
  AFMetadataURL: "/geonetwork/srv/eng/catalog.search#/metadata/c4b6504f-5d54-4b61-a745-4123fae873ec",
  FTMetadataURL: "",
  spatialUnitLayers:[],// populated on App load: ams.App.run(...)
  floatDecimals: 2,// change this number to change the number of decimals to float numbers
  propertyName: {
    deter: "area",
    af: "counts",
    rk: "counts",
    ri: "score",
    fs: "units",
    ft: "counts",
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
  deter: "deter-ams",
  activeFire:"active-fire",
  activeFireToday:"active-fire-today",
  lastDate: "last_date",
  inpeRisk: "risk-inpe-data",
  fireSpreadingRisk: "fire-spreading-risk"
};

const defaultFilters = {
  spatialUnit: 'cs_150km',
  temporalUnit: '7d',
  // can be 'onPeriod' or 'periodDiff'
  diffClassify: 'onPeriod',
  priorityLimit: 10
};

const defaultRiskFilter = {
  source: "inpe",
  threshold: parseFloat(ams.Utils.getServerConfigParam('risk_threshold')),
  expirationRisk: 7,
  scaleFactor: parseFloat(ams.Utils.getServerConfigParam('risk_scale_factor'))
};

const defaultWorkspace = ams.Utils.isHomologationEnvironment()? "ams1" : "ams3";

// configuration by biome
ams.BiomeConfig["Amazônia"] = {
  defaultWorkspace: defaultWorkspace,
  defaultLayers: defaultLayers,
  defaultFilters: {
    ...defaultFilters,
    // can be group's name of DETER classnames, 'DS', 'DG', 'CS' and 'MN', or 'AF' to Queimadas, or 'RI' to INPE risk
    indicator: 'DS',
  },
  defaultRiskFilter: defaultRiskFilter
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
ams.BiomeConfig["ALL"] = {...activeFiresLayerConfig, ...defaultConfig};
ams.BiomeConfig["all"] = {...activeFiresLayerConfig, ...defaultConfig};
