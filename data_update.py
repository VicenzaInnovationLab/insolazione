import os
from pathlib import Path
import glob
import json
import requests as r
from datetime import datetime as dt
import numpy as np

import geopandas as gpd
import pandas as pd
import rasterio

from logger import custom_log
import config as cfg


# >IMPOSTAZIONI INIZIALI<

# Attivare logging
log = custom_log(__file__)
log.critical("L'ESECUZIONE INIZIA")


def latest_file(folder: str, fpattern: str) -> str:
    """Ottiene l'ultimo JSON dalla cartella specificata"""
    list_of_files = glob.glob(f"{folder}\{fpattern}")
    if len(list_of_files) > 0:
        last_file = max(list_of_files, key=os.path.getctime)
        return last_file
    else:
        log.error(f"non c'è nessun file che corrisponde al pattern specificato: '{folder}\{fpattern}'")
        raise SystemExit(1)


now_str = dt.now().strftime("%Y%m%d-%H%M%S")  # il marcatempo per aggiungere nei nomi di file
adm_list = {"Creazzo", "Altavilla Vicentina", "Sovizzo", "Torri di Quartesolo"}


log.info(f"STEP 1. INTERROGAZIONE DEL GEOPORTALE REGIONALE")

if cfg.SKIP_DOWNLOAD:  # Prendere l'ultimo JSON dalla cartella 'processing\download'
    log.warn("download dal Geoportale è disattivato")
    wfs_file = latest_file("processing\download", "edifici_reg*.json")
    if Path(wfs_file).is_file():
        log.info(f"è trovato '{wfs_file}'")
    else:
        log.error(f"non c'è nessun JSON con gli edifici dal Geoportale: controlla la cartella 'download' e nomi di file")
        raise SystemExit(1)

else:  # Scaricare edifici dal Geoportale Regionale
    try:
        wfs_params = dict(service="WFS",
                          version="2.0.0",
                          request="GetFeature",
                          outputFormat="JSON",
                          typenames=f"rv:{cfg.EDIFLAYER}",
                          srsname=cfg.SRSNAME,
                          bbox=cfg.BBOX)

        req = r.get(cfg.ENDPOINT_REG, params=wfs_params)
        log.info(f"URL della richiesta: {req.url}")
        edif_wfs = req.json()
        log.info(f"ci sono {edif_wfs['totalFeatures']} edifici in totale nel Bounding Box")
    except Exception as e:
        log.error(e)
        raise SystemExit(1)

    # Salvare il file scaricato
    wfs_file = f"processing\download\edifici_reg_{now_str}.json"
    try:
        with open(wfs_file, "w") as f:
            json.dump(edif_wfs, f)
        log.info(f"'{wfs_file}' è salvato")
    except Exception as e:
        log.error(f"è impossibile salvare '{wfs_file}': {e}")
        raise SystemExit(1)


log.info(f"STEP 2. FUSIONE DEGLI EDIFICI")

# Leggere i file
try:
    adm_prov = gpd.read_file(f"processing\comuni_provincia_vi_7795.zip")
    adm = adm_prov[adm_prov["comune"].isin(adm_list)]
    log.info(f"sono estratti {len(adm)} poligoni dei comuni")

    edif_reg = gpd.read_file(wfs_file).to_crs(7795)
    log.info(f"sono letti {len(edif_reg)} edifici dallo '{wfs_file}'")

    edif_vi = gpd.read_file(f"processing\edifici_sitvi_7795.zip")
    log.info(f"sono letti {len(edif_vi)} edifici SIT VI")
except Exception as e:
    log.error(f"è impossibile aprire i file vettoriali necessari: {e}")
    raise SystemExit(1)

# Intersezione spaziale
try:
    log.info(f"è iniziata l'intersezione degli edifici dal Geoportale regionale con i poligoni comunali...")
    edif_reg_filt = gpd.overlay(edif_reg, adm, how="intersection")
    log.info(f"l'intersezione è andata a buon fine")
except Exception as e:
    log.error(f"è impossibile incrociare gli edifici dal Geoportale regionale con i poligoni comunali: {e}")
    raise SystemExit(1)

# Trasformazione degli attributi
try:
    log.info(f"è iniziata la trasformazione degli attributi...")

    edif_reg_filt["tipo"] = np.where(edif_reg_filt["edi_uso"] == "01", "residenziale", "non residenziale")
    edif_reg_filt.rename(columns={"fid": "orig_id"}, inplace=True)
    edif_reg_filt = edif_reg_filt[["orig_id", "tipo", "comune", "geometry"]]

    edif_vi["tipo"] = np.where(edif_vi["Uso"] == "residenziale", "residenziale", "non residenziale")
    edif_vi.rename(columns={"gid": "orig_id", }, inplace=True)
    edif_vi["comune"] = "Vicenza"
    edif_vi = edif_vi[["orig_id", "tipo", "comune", "geometry"]]

    edifici_uniti = gpd.GeoDataFrame(
        pd.concat([edif_vi, edif_reg_filt], ignore_index=True),
        crs=edif_vi.crs)
    edifici_uniti["area"] = edifici_uniti.area
    log.info(f"la trasformazione degli attributi di edifici è andata a buon fine ")
except Exception as e:
    log.error(f"è impossibile trasformare gli attributi di edifici: {e}")
    raise SystemExit(1)

# Salvare il risultato
log.warn("raster con insolazione filtrato sarà sovrascritto")
try:
    edifici_uniti_name = f"processing\output\edifici_uniti.json"
    edifici_uniti.to_file(edifici_uniti_name, driver="GeoJSON")
    log.info(f"il file '{edifici_uniti_name}' è salvato")
except Exception as e:
    log.error(f"è impossibile salvare il risultato finale: {e}")
    raise SystemExit(1)


log.info(f"STEP 3. PREPARAZIONE DATI RASTER")

if cfg.SKIP_RASTER:
    log.warn("elaborazione del raster è disattivato")
    ins_file = latest_file("processing\output", "insolazione_filtrato.tif")
    if Path(ins_file).is_file():
        log.info(f"è trovato '{ins_file}'")
    else:
        log.error(f"non c'è nessun RASTER dell'insolazione filtrato: controlla la cartella 'processing\output' e nomi di file")
        raise SystemExit(1)
else:
    log.warn("raster con insolazione filtrato sarà sovrascritto")
    try:
        # aprire i file raster in Read mode
        insol_ = rasterio.open(cfg.INSOLAZIONE)
        insol = insol_.read(1)
        pend = rasterio.open(cfg.PENDENZA).read(1)
        espos = rasterio.open(cfg.ESPOSIZIONE).read(1)

        log.info(f"i file raster sono letti")

        # estrarre l'area di un pixel, in metri quadri
        pixel_size_x, pixel_size_y = insol_.res
        pixel_area = pixel_size_x * pixel_size_y

        log.info(f"eseguo Map Algebra - mascheratura di valori raster...")
        insol_f = np.where(
                (np.greater_equal(insol, cfg.MIN_INS)
                 & np.less_equal(pend, cfg.MAX_PEND)
                 & np.greater_equal(espos, cfg.MIN_ESP)
                 & np.less_equal(espos, cfg.MAX_ESP)
                 ),
                insol,
                -9999)
        log.info(f"l'insolazione irrelevante è stata filtrata")
    except Exception as e:
        log.error(f"è impossibile elaborare i dati raster: {e}")
        raise SystemExit(1)

    log.info(f"insolazione irrelevante è stata filtrata")

    log.info(f"eseguo salvataggio dell'insolazione elaborata")
    try:
        with rasterio.open(
                f"processing/output/insolazione_filtrato.tif",
                "w",
                driver="GTiff",
                height=insol_f.shape[0],
                width=insol_f.shape[1],
                count=1,
                dtype=insol_f.dtype,
                crs=insol_.crs,
                transform=insol_.transform
        ) as dst:
            dst.write_band(1, insol_f)
    except Exception as e:
        log.error(f"è impossibile salvare il raster elaborato: {e}")
        raise SystemExit(1)

log.info(f"STEP 4. STATISTICHE ZONALI")
# TODO: statistiche zonali

log.critical("L'ESECUZIONE È FINITA CON SUCCESSO")
