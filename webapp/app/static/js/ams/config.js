var ams = ams || {};

ams.Config = {
  terrabrasilisURL:"http://terrabrasilis.dpi.inpe.br",
  defaultLayers:{
    amzBiomeBorder:"prodes-amz:brazilian_amazon_biome_border",// Layer name of Amazon biome border from TerraBrasilis service
    deterAmz:"deter-ams" // Layer name of DETER alerts from TerraBrasilis service
  },
  floatDecimals: 2,// change this number to change the number of decimals to float numbers
	DETERMetadataURL: "/geonetwork/srv/eng/catalog.search#/metadata/f9b7e1d3-0d4e-4cb1-b3cf-c2b8906126be"
};