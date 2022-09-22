<?xml version="1.0" encoding="ISO-8859-1"?>
<StyledLayerDescriptor version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd" xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <NamedLayer>
        <Name>active-fire</Name>
        <UserStyle>
            <Title>Active Fires Point</Title>
            <Abstract>A point style that represents an active fire</Abstract>
            <FeatureTypeStyle>
                <Rule>
                    <Name>Large</Name>
                    <Title>Focos</Title>
                    <MaxScaleDenominator>160000000</MaxScaleDenominator>
                    <PointSymbolizer>
                        <Graphic>
                            <Mark>
                                <WellKnownName>circle</WellKnownName>
                                <Fill>
                                    <CssParameter name="fill">#ffff00</CssParameter>
                                    <CssParameter name="fill-opacity">0.8</CssParameter>
                                </Fill>
                                <Stroke>
                                    <CssParameter name="stroke">#ff0000</CssParameter>
                                    <CssParameter name="stroke-width">1</CssParameter>
                                </Stroke>
                            </Mark>
                            <Size>6</Size>
                        </Graphic>
                    </PointSymbolizer>
                </Rule>
                <Rule>
                    <Name>Medium</Name>
                    <Title>Focos</Title>
                    <MinScaleDenominator>160000000</MinScaleDenominator>
                    <MaxScaleDenominator>320000000</MaxScaleDenominator>
                    <PointSymbolizer>
                        <Graphic>
                            <Mark>
                                <WellKnownName>circle</WellKnownName>
                                <Fill>
                                    <CssParameter name="fill">#ffff00</CssParameter>
                                    <CssParameter name="fill-opacity">0.8</CssParameter>
                                </Fill>
                                <Stroke>
                                    <CssParameter name="stroke">#ff0000</CssParameter>
                                    <CssParameter name="stroke-width">1</CssParameter>
                                </Stroke>
                            </Mark>
                            <Size>4</Size>
                        </Graphic>
                    </PointSymbolizer>
                </Rule>
                <Rule>
                    <Name>Small</Name>
                    <Title>Focos</Title>
                    <MinScaleDenominator>320000000</MinScaleDenominator>
                    <PointSymbolizer>
                        <Graphic>
                            <Mark>
                                <WellKnownName>circle</WellKnownName>
                                <Fill>
                                    <CssParameter name="fill">#ffff00</CssParameter>
                                    <CssParameter name="fill-opacity">0.8</CssParameter>
                                </Fill>
                                <Stroke>
                                    <CssParameter name="stroke">#ff0000</CssParameter>
                                    <CssParameter name="stroke-width">1</CssParameter>
                                </Stroke>
                            </Mark>
                            <Size>2</Size>
                        </Graphic>
                    </PointSymbolizer>
                </Rule>
            </FeatureTypeStyle>
        </UserStyle>
    </NamedLayer>
</StyledLayerDescriptor>