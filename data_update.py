import os
import glob
import json
import requests as r
from datetime import datetime as dt

import geopandas as gpd

from logger import custom_log
from config import ENDPOINT_REG, LAYER, BBOX, SRSNAME, EDIF_VI, ADM_VI, DOWNLOAD


# FUNZIONI
def latest_edif_reg(fpath: str) -> str:
    """Ottiene l'ultimo JSON dalla cartella specificata"""
    list_of_jsons = glob.glob(f"{fpath}/edifici_veneto*.json")
    json_file = max(list_of_jsons, key=os.path.getctime)
    return json_file


# LOGGING
log = custom_log(__file__)
log.critical("inizio aggiornamento degli edifici")


# INTERROGAZIONE DEL GEOPORTALE REGIONALE

if DOWNLOAD:
    try:
        wfs_params = dict(service="WFS",
                          version="2.0.0",
                          request="GetFeature",
                          outputFormat="JSON",
                          typenames=f"rv:{LAYER}",
                          srsname=SRSNAME,
                          bbox=BBOX)
        log.info(f"Sto interrogando {ENDPOINT_REG}...")
        req = r.get(ENDPOINT_REG, params=wfs_params)
        log.debug(req.url)
        edif_wfs = req.json()
        log.info(f"Ho ottenuto {edif_wfs['totalFeatures']} edifici in totale dallo strato rv:{LAYER}")
    except Exception as e:
        log.error("qualcosa non è andato bane ", e)
        raise SystemExit()

    # Nome unico con il timestamp attuale per il JSON scaricato
    now = dt.now()
    now_str = now.strftime("%Y%m%d-%H%M%S")
    wfs_file = f"download/{LAYER}_{now_str}.json"

    # Salvare il file
    try:
        with open(wfs_file, "w") as f:
            json.dump(edif_wfs, f)
        log.info(f"'{wfs_file}' dal Geoportale è salvato")
    except Exception as e:
        log.error(f"non posso salvare '{wfs_file}' ", e)
        raise SystemExit()

# Prendere l'ultimo json dalla cartella 'download'
else:
    try:
        wfs_file = latest_edif_reg("download")
    except Exception as e:
        log.error(f"Non posso specificare l'ultimo JSON con gli edifici regionali. Verifica la cartella 'download' ", e)
        raise SystemExit()


# FUSIONE DEGLI EDIFICI DI VICENZA CON GLI EDIFICI REGIONALI

# Leggere i file
try:
    adm_vi = gpd.read_file(f"download/{ADM_VI}.json")
    adm = adm_vi[adm_vi["comune"] != "VICENZA"]
    log.info(f"Sono letti {len(adm)} poligoni dei comuni")

    edif_reg = gpd.read_file(wfs_file).to_crs(7795)
    log.info(f"Sono letti {len(edif_reg)} edifici dallo file dal Geoportale regionale")

    edif_vi = gpd.read_file(f"download/{EDIF_VI}.zip")
    log.info(f"Sono letti {len(edif_vi)} edifici dallo Shapefile dal SIT VI")
except Exception as e:
    log.error(f"Non posso aprire tutti i file necessari ", e)
    raise SystemExit()

# Relazione spaziale
try:
    edif_reg_filt = gpd.overlay(edif_reg, adm, how="intersection")
    edif = edif_reg_filt
    log.info(f"Intersezione degli edifici è andata a buon fine ")
except Exception as e:
    log.error(f"Non posso incrociare gli edifici regionali con gli edifici comunali ", e)
    raise SystemExit()

# Salvare il risultato
try:
    edif.to_file("download/res_union.json", driver="GeoJSON")
    log.critical("Ho aggiornato gli edifici con successo")
except Exception as e:
    log.error(f"Non posso salvare il risultato ", e)
    raise SystemExit()
