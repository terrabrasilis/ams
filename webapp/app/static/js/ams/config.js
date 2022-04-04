var ams = ams || {};

ams.Config = {
  terrabrasilisURL:"http://terrabrasilis.dpi.inpe.br",
  DETERMetadataURL: "/geonetwork/srv/eng/catalog.search#/metadata/f9b7e1d3-0d4e-4cb1-b3cf-c2b8906126be",
  defaultLayers:{
    biomeBorder:"prodes-amz:brazilian_amazon_biome_border",// Layer name of Amazon biome border from TerraBrasilis service
    deterAmz:"deter-ams", // The layer name of DETER alerts from TerraBrasilis service. The workspace is dinamic and based on authentication state
    activeFireAmz:"ams:active-fire" // The layer name of Focos de Queimadas from TerraBrasilis service. The workspace is fixed
  },
  spatialUnitLayers:[],// populated on App load: ams.App.run(...)
  floatDecimals: 2,// change this number to change the number of decimals to float numbers
  defaultFilters: {
    indicator: 'DS',// can be group's name of DETER classnames, 'DS', 'DG', 'CS' and 'MN', or 'AF' to Queimadas
    spatialUnit: 'csAmz_150km',
    temporalUnit: '7d',
    diffClassify: 'onPeriod'// can be 'onPeriod' or 'periodDiff'
  },
  propertyName: {
    deter:"area",// can be "area", if reference layer is DETER
    af:"counts" // or "counts", if reference layer is AF - Active Fire (Focos de Queimadas)
  }
};