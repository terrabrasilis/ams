var ams = ams || {};

ams.Config = {
  terrabrasilisURL:"http://terrabrasilis.dpi.inpe.br",
  defaultLayers:{
    biomeBorder:"prodes-amz:brazilian_amazon_biome_border",// Layer name of Amazon biome border from TerraBrasilis service
    deterAmz:"deter-ams", // Layer name of DETER alerts from TerraBrasilis service. The workspace is dinamic and based on authentication state
    activeFireAmz:"ams:active-fire"
  },
  spatialUnitLayers:[],// populated on App load: ams.App.run(...)
  floatDecimals: 2,// change this number to change the number of decimals to float numbers
	DETERMetadataURL: "/geonetwork/srv/eng/catalog.search#/metadata/f9b7e1d3-0d4e-4cb1-b3cf-c2b8906126be",
  defaultFilters: {
    indicator: 'DS',
    spatialUnit: 'csAmz_150km',
    temporalUnit: '7d',
    diffClassify: 'onPeriod'
  }
};