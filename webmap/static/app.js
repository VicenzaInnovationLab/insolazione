function onEachFeature(feature, layer) {
    var popupContent = "<ul><li>Questo edificio può generare <b>" +
            Math.round(feature.properties.elec_prod_mwh) + " MW·h</b> da fotovoltaici in un anno</li>" +
            "<li>Codice edificio: <b>" + feature.properties.codice_edificio + "</b></li>" +
            "<li>Uso: <b>" + feature.properties.uso + "</b></li></ul>";
    layer.bindPopup(popupContent);
}

function stileEdifici(feature) {
        var val = feature.properties.elec_prod_mwh;
        if (val < 50) {
            return {color: "#000000", fillColor: "#fef0d9", opacity: 1.0, fillOpacity: 0.8, weight: 0.4};
        } else if (50 <= val && val < 200) {
            return {color: "#000000", fillColor: "#fdcc8a", opacity: 1.0, fillOpacity: 0.8, weight: 0.4};
        } else if (200 <= val && val < 800) {
            return {color: "#000000", fillColor: "#fc8d59", opacity: 1.0, fillOpacity: 0.8, weight: 0.4};
        } else if (800 <= val && val < 3200) {
            return {color: "#000000", fillColor: "#e34a33", opacity: 1.0, fillOpacity: 0.8, weight: 0.4};
        } else if (3200 <= val && val < 12000) {
            return {color: "#000000", fillColor: "#b30000", opacity: 1.0, fillOpacity: 0.8, weight: 0.4};
        }
}

var edifici = L.geoJSON(edificiInsolazione,
    {style: stileEdifici, onEachFeature: onEachFeature,
    attribution: "Elaborazione Digital Surface Model MATTM - Geoportale nazionale &copy; " +
        "<a href=\"https://digitalinnovationhubvicenza.it\">Digital Innovation Hub Vicenza</a>"});

var vicenza = L.geoJSON(confiniVi,
    {style: {color: "#ccc", opacity: 0.9, fillOpacity: 0.0, weight: 2},
    attribution: "Confini di Vicenza &copy; " +
        "<a href=\"http://sit.comune.vicenza.it/SitVI/vicenza/index.php\">SitVI</a>"});

var mbToken = "pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw"
var mbAttr = "Dati cartografici &copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors, " +
    "Immagini satellitari © <a href='https://www.mapbox.com/'>Mapbox</a>",
    mbUrl = "https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token=" + mbToken;

var dark = L.tileLayer(mbUrl, {id: 'mapbox/dark-v9', tileSize: 512, zoomOffset: -1, attribution: mbAttr}),
    strade = L.tileLayer(mbUrl, {id: 'mapbox/streets-v11', tileSize: 512, zoomOffset: -1, attribution: mbAttr}),
    satellite = L.tileLayer(mbUrl, {id: 'mapbox/satellite-v9', tileSize: 512, zoomOffset: -1, attribution: mbAttr});

var corner1 = L.latLng(45.4335, 11.4307),
    corner2 = L.latLng(45.6519, 11.6769),
    bounds = L.latLngBounds(corner1, corner2);

var map = L.map("map", {
    center: [45.548, 11.548], // Vicenza
    zoom: 14,
    minZoom: 13,
    maxZoom: 18,
    maxBounds: bounds,
    layers: [dark, vicenza, edifici]
});

var baseLayers = {
    "Basemap scuro": dark,
    "Strade": strade,
    "Satellite": satellite
};

var overlays = {
    "Edifici": edifici,
    "Limiti amministrativi": vicenza
};

L.control.layers(baseLayers, overlays).addTo(map);

L.Control.Watermark = L.Control.extend({
    onAdd: function(map) {
        var img = L.DomUtil.create("img");

        img.src = "static/images/logo.png";
        img.style.width = "300px";

        return img;
    },

    onRemove: function(map) {
        // Nothing to do here
    }
});

L.control.watermark = function(opts) {return new L.Control.Watermark(opts);}
L.control.watermark({ position: "bottomright" }).addTo(map);
L.control.scale().addTo(map);
