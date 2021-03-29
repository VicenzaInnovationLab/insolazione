# insolazione
La mappa interattiva dell'insolazione di Vicenza nel sistema EPSG:7795.
Lo script `data_update.py` prepara un geojson con edifici per i comuni di Vicenza, Creazzo, Altavilla Vicentina, Sovizzo e Torri di Quartesolo. I dati per Vicenza si prende dal SIT VI 2.0, mentre per altri comuni si usa il geoportale regionale.

## Installazione

1. Installa GDAL - [scarica](https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal) la versione relevante al tuo Python e architettura dell'OS:


    pip install dependencies\GDAL-3.2.2-cp39-cp39-win_amd64.whl

2. Installa **Microsoft Visual C++** 14.0 (o maggiore). Scaricalo con lo strumento ["Microsoft C++ Build Tools"](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

3. Installa altre librerie Python:
   pip install numpy requests rasterstats

È importante installare i seguenti librerie in ordine:

    pip install dependencies\GDAL-3.2.2-cp39-cp39-win_amd64.whl
    pip install dependencies\pyproj-3.0.1-cp39-cp39-win_amd64.whl
    pip install dependencies\Fiona-1.8.18-cp39-cp39-win_amd64.whl
    pip install dependencies\Shapely-1.7.1-cp39-cp39-win_amd64.whl
    pip install dependencies\geopandas-0.9.0-py3-none-any.whl
    pip install dependencies\Rtree-0.9.7-cp39-cp39-win_amd64.whl
    pip install dependencies\rasterio-1.2.1-cp39-cp39-win_amd64.whl
    pip install dependencies\rasterio-1.2.1-cp39-cp39-win_amd64.whl

## Requisiti preliminari

1. Metti l'archivio `processing/edifici_sitvi_7795.zip` con uno Shapefile di edifici, scaricati dal [SIT VI](http://sit.comune.vicenza.it/SitVI/SitVi_conf/download/index.php) con i seguenti parametri:
   - gruppo `Cartografia di base`
   - file `Edifici`
   - format `ESRI Shapefile`
   - Sistema di riferimento `RDN2008 - Zone12 (EPSG 7795)`
   - Nome file di output `edifici_sitvi_7795`
    
2. Assicurati che c'è anche l'archivio `processing/comuni_provincia_vi_7795.zip` che contiene i limiti amministrativi necessari.

3. Controlla le impostazioni nel `config.py`: serve specificare i percorsi corretti nella sezione *RASTER*.

## Steps

1. Interrogazione del Geoportale Regionale per scraricare gli edifici sul territorio di Creazzo, Altavilla Vicentina, Sovizzo e Torri di Quartesolo.
2. Fusione degli edifici dal SIT VI e il Geoportale regionale al fine di creare uno strato vettoriale uniforme.