var geojsonFeature = "data/edifici.geojson"
var cities = L.layerGroup();

L.marker([39.61, -105.02]).bindPopup('This is Littleton, CO.').addTo(cities),
    L.marker([39.74, -104.99]).bindPopup('This is Denver, CO.').addTo(cities),
    L.marker([39.73, -104.8]).bindPopup('This is Aurora, CO.').addTo(cities),
    L.marker([39.77, -105.23]).bindPopup('This is Golden, CO.').addTo(cities);

var mbToken = "pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw"
var mbAttr = "Map data &copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors, " +
    "Imagery © <a href='https://www.mapbox.com/'>Mapbox</a>",
    mbUrl = "https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token=" + mbToken;

var dark = L.tileLayer(mbUrl, {id: 'mapbox/dark-v9', tileSize: 512, zoomOffset: -1, attribution: mbAttr}),
    strade = L.tileLayer(mbUrl, {id: 'mapbox/streets-v11', tileSize: 512, zoomOffset: -1, attribution: mbAttr}),
    satellite = L.tileLayer(mbUrl, {id: 'mapbox/satellite-v9', tileSize: 512, zoomOffset: -1, attribution: mbAttr});
;

var map = L.map('map', {
    center: [45.548, 11.548,], // Vicenza
    zoom: 14,
    layers: [dark, cities]
});

var baseLayers = {
    "Dark": dark,
    "Strade": strade,
    "Satellite": satellite
};

var overlays = {
    "Cities": cities
};

L.control.layers(baseLayers, overlays).addTo(map);
L.geoJSON(geojsonFeature).addTo(map);