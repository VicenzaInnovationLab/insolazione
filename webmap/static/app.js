// LAYER LOCALI
var edifici_vi = L.geoJSON(edifici,
  {
    style: stileEdifici, onEachFeature: onEachFeature,
    attribution: "Elaborazione del modello digitale di elevazione MATTM - Geoportale nazionale &copy; " +
      "<a href=\"https://digitalinnovationhubvicenza.it\">Digital Innovation Hub Vicenza</a>"
  });

var comuni_vi = L.geoJSON(comuni,
  {
    style: {color: "#ccc", opacity: 0.9, fillOpacity: 0.0, weight: 2},
    attribution: "Confini comunali della provincia di Vicenza &copy; " +
      "<a href=\"http://sit.comune.vicenza.it/SitVI/vicenza/index.php\">SitVI</a>"
  });

// LAYER INTERNET
var mbToken = "pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw"
var mbAttr = "Dati cartografici &copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors, " +
  "Immagini satellitari © <a href='https://www.mapbox.com/'>Mapbox</a>",
  mbUrl = "https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token=" + mbToken;

var dark = L.tileLayer(mbUrl, {
    id: 'mapbox/dark-v9',
    tileSize: 512,
    zoomOffset: -1,
    attribution: mbAttr
  }),
  strade = L.tileLayer(mbUrl, {
    id: 'mapbox/streets-v11',
    tileSize: 512,
    zoomOffset: -1,
    attribution: mbAttr
  }),
  satellite = L.tileLayer(mbUrl, {
    id: 'mapbox/satellite-v9',
    tileSize: 512,
    zoomOffset: -1,
    attribution: mbAttr
  });

var corner1 = L.latLng(45.4538, 11.3961),
  corner2 = L.latLng(45.6285, 11.6678),
  bbox = L.latLngBounds(corner1, corner2);

// MAPPA
var map = L.map("map", {
  center: [45.548, 11.548], // Vicenza
  zoom: 13,
  minZoom: 12,
  maxZoom: 18,
  maxBounds: bbox,
  layers: [dark, comuni_vi, edifici_vi]
});

var baseLayers = {
  "Basemap scuro": dark,
  "Strade": strade,
  "Satellite": satellite
};

var overlays = {
  "Edifici": edifici_vi,
  "Comuni": comuni_vi
};

L.Control.Watermark = L.Control.extend({
    onAdd: function(map) {
        var img = L.DomUtil.create("img");

        img.src = "static/images/logo-innovationlab.png";
        img.style.width = "300px";

        return img;
    },

    onRemove: function(map) {
        // Nothing to do here
    }
});

// Geosearch
L.Control.geocoder({
  placeholder: "Trova indirizzo...",
  geocoder: L.Control.Geocoder.nominatim({
    geocodingQueryParams: {
      countrycodes: "it",
      "accept-language": "it",
      viewbox: bbox.toBBoxString(),  // y1, x1, y2, x2
      bounded: 1
    }
  }),
  position: "topleft",
  collapsed: false,
  expand: "hover"
}).addTo(map);

L.control.watermark = function(opts) {return new L.Control.Watermark(opts);}
L.control.watermark({ position: "bottomleft" }).addTo(map);
// L.control.scale({ position: "bottomleft" }).addTo(map);
map.zoomControl.setPosition("topleft");

// STILE INTERATTIVO PER GLI EDIFICI
function stileEdifici(feature) {
  var val = feature.properties.elett_prod_mwh;
  if (val < 50) {
    return {
      color: "#000000",
      fillColor: "#fef0d9",
      opacity: 1.0,
      fillOpacity: 0.8,
      weight: 0.4
    };
  } else if (50 <= val && val < 200) {
    return {
      color: "#000000",
      fillColor: "#fdcc8a",
      opacity: 1.0,
      fillOpacity: 0.8,
      weight: 0.4
    };
  } else if (200 <= val && val < 800) {
    return {
      color: "#000000",
      fillColor: "#fc8d59",
      opacity: 1.0,
      fillOpacity: 0.8,
      weight: 0.4
    };
  } else if (800 <= val && val < 3200) {
    return {
      color: "#000000",
      fillColor: "#e34a33",
      opacity: 1.0,
      fillOpacity: 0.8,
      weight: 0.4
    };
  } else if (3200 <= val) {
    return {
      color: "#000000",
      fillColor: "#b30000",
      opacity: 1.0,
      fillOpacity: 0.8,
      weight: 0.4
    };
  }
}

function getColor(val) {
  return (val < 50) ? '#fef0d9' :
    (50 <= val && val < 200) ? '#fdcc8a' :
      (200 <= val && val < 800) ? '#fc8d59' :
        (800 <= val && val < 3200) ? '#e34a33' :
          (3200 <= val) ? '#b30000' :
            '#000000';
}

// Facciamo gli edifici evidenziati visivamente in qualche modo quando vengono toccati dal mouse
function highlightFeature(e) {
  var layer = e.target;

  layer.setStyle({
    weight: 1,
    color: "#fff",
    dashArray: "",
    fillOpacity: 1
  });

  if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
    layer.bringToFront();
  }
  info.update(layer.feature.properties);
}

// Definiremo cosa succede su Mouseout:
function resetHighlight(e) {
  edifici_vi.resetStyle(e.target);
  info.update();
}

// Definiamo un Listener di click che ingrandisce l'edificio
function zoomToFeature(e) {
  map.fitBounds(e.target.getBounds());
}

// Ora useremo l'opzione OnEachFeature per aggiungere i listener sul nostro livello di edifici:
function onEachFeature(feature, layer) {
  layer.on({
    mouseover: highlightFeature,
    mouseout: resetHighlight,
    click: zoomToFeature
  });
}

// CONTROLLO ATTRIBUTI POPUP PERSONALIZZATO
var info = L.control();

info.onAdd = function (map) {
  this._div = L.DomUtil.create("div", "info");  // crea un div con una classe "info"
  this.update();
  return this._div;
};

// metodo che useremo per aggiornare il controllo in base agli attributi degli edifici passati
info.update = function (props) {
  this._div.innerHTML = "<h4>Generazione da fotovoltaico</h4>" + (props ?
    "<b>" + Math.round(props.elett_prod_mwh) + " MW·h annui" + "</b><br />" +
    "Tipo: " + props.tipo + "<br />Comune: " + props.comune
    : "Passa il mouse sopra un edificio");
};

info.addTo(map);

// CONTROLLO DELLA LEGENDA PERSONALIZZATA
var legend = L.control({position: "bottomright"});

legend.onAdd = function (map) {

  var div = L.DomUtil.create("div", "info legend"),
    grades = [0, 50, 200, 800, 3200],
    label = [];

  div.innerHTML = "<h4>MW·h annui</h4>"
  // Loop attraverso i nostri intervalli di 'elett_prod_mwh' e genera un'etichetta con un quadrato colorato per ogni intervallo
  for (var i = 0; i < grades.length; i++) {
    div.innerHTML +=
      '<i style="background:' + getColor(grades[i] + 1) + '"></i> ' +
      grades[i] + (grades[i + 1] ? '&ndash;' + grades[i + 1] + '<br>' : '+');
  }

  return div;
};

legend.addTo(map);

L.control.layers(baseLayers, overlays, options = {position: "bottomright"}).addTo(map);

// About
var aboutText =
  `<p>Il progetto è parte del Operativo Regionale del Fondo Europeo di Sviluppo Regionale 
  (POR FESR 2014 - 2020) del Veneto, nell'ambito del bando dell'azione 231 volto alla 
  \"costituzione di Innovation Lab diretti al consolidamento/sviluppo del network 
  Centri P3@-Palestre Digitali e alla diffusione della cultura degli Open Data\".</p>
  <p><a href='https://github.com/dihvicenza/insolazione'>Più informazioni</a></p>`


var showAbout = function () {
  Swal.fire({
    title: "InnovationLab Vicenza",
    html: aboutText,
    imageUrl: "static/images/logo.png",
    imageWidth: 800,
    imageAlt: "Logo InnovationLab Vicenza",
    footer:
      `<p>La web app è sviluppata dal <a href='https://digitalinnovationhubvicenza.it/'> 
      Digital Innovation Hub</a> di Confartigianato Vicenza.</p> 
      <p>Il favicon del sito è creato da <a href='www.freepik.com'>Freepik</a> 
      dal www.flaticon.com.</p>`
  });
}

L.easyButton("fa-info", showAbout).addTo(map);
