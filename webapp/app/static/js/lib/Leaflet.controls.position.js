var ams = ams || {};

ams.LeafletControlPosition = {
    addNewPositions: function(map){
        var corners = map._controlCorners = {},
        l = 'leaflet-',
        container = map._controlContainer =
            L.DomUtil.create('div', l + 'control-container', map._container);

        function createCorner(vSide, hSide) {
            var className = l + vSide + ' ' + l + hSide;
            corners[vSide + hSide] = L.DomUtil.create('div', className, container);
        }

        createCorner('top', 'left');
        createCorner('top', 'right');
        createCorner('bottom', 'left');
        createCorner('bottom', 'right');

        createCorner('top', 'center');
        createCorner('middle', 'center');
        createCorner('middle', 'left');
        createCorner('middle', 'right');
        createCorner('bottom', 'center');
    }
};