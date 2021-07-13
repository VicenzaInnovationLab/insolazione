import os
import pprint
from pathlib import Path
import glob
import json
import requests as r
from datetime import datetime as dt
import numpy as np

import geopandas as gpd
import pandas as pd
import rasterio as rst
from rasterstats import zonal_stats

from logger import custom_log
import config as cfg


# || IMPOSTAZIONI INIZIALI

# Attivare logging
log = custom_log(__file__)
log.critical("L'ESECUZIONE INIZIA")


def latest_file(folder: str, fpattern: str) -> str:
    """Ottiene l'ultimo JSON dalla cartella specificata"""
    list_of_files = glob.glob(f"{folder}\\{fpattern}")
    if len(list_of_files) > 0:
        last_file = max(list_of_files, key=os.path.getctime)
        return last_file
    else:
        log.error(f"non c'è nessun file che corrisponde al pattern specificato: '{folder}\\{fpattern}'")
        raise SystemExit(1)


def get_zonal_stats(vector, raster, stats, nodata, affine_):
    """Esegue le statistiche zonali e salva il risultato in Geopandas DataFrame"""
    result = zonal_stats(vector, raster, nodata=nodata, stats=stats, affine=affine_, geojson_out=True)
    geostats = gpd.GeoDataFrame.from_features(result, crs=vector.crs)
    return geostats


now_str = dt.now().strftime("%Y%m%d-%H%M%S")  # il marcatempo per aggiungerli in nomi di file
adm_list = {"Creazzo", "Altavilla Vicentina", "Sovizzo", "Torri di Quartesolo"}

# || ELABORAZIONE DATI

log.info(f"STEP 1. INTERROGAZIONE DEL GEOPORTALE REGIONALE")

if cfg.SKIP_DOWNLOAD:  # Prendere l'ultimo JSON dalla cartella 'processing\download'
    log.warning("download dal Geoportale è disattivato")
    wfs_file = latest_file("..\data\download", "edifici_reg*.json")
    if Path(wfs_file).is_file():
        log.info(f"viene usato '{wfs_file}'")
    else:
        log.error("non c'è nessun JSON con gli edifici dal Geoportale: controlla la cartella 'download' e nomi di file")
        raise SystemExit(1)

else:  # Scaricare edifici dal Geoportale Regionale
    try:
        wfs_params = dict(service="WFS",
                          version="2.0.0",
                          outputFormat="JSON",
                          request="GetFeature",
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
    wfs_file = f"..\data\download\edifici_reg_{now_str}.json"
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
    adm_prov = gpd.read_file(f"..\data\comuni_provincia_vi_7795.zip")
    adm = adm_prov[adm_prov["comune"].isin(adm_list)]
    nodata_mask = gpd.read_file(f"..\data\lidar_nodata_mask.zip")
    log.info(f"sono estratti {len(adm)} poligoni dei comuni contermini a Vicenza")

    log.info("lettura del file dal Geoportale Regionale...")
    edif_reg = gpd.read_file(wfs_file).to_crs(7795)
    log.info(f"sono letti {len(edif_reg)} edifici dal Geoportale regionale")

    edif_vi = gpd.read_file(f"..\data\edifici_sitvi_7795.zip")
    log.info(f"sono letti {len(edif_vi)} edifici SIT VI")
except Exception as e:
    log.error(f"è impossibile aprire i file vettoriali necessari: {e}")
    raise SystemExit(1)

# Intersezione spaziale
try:
    log.info(f"è iniziata l'intersezione degli edifici dal Geoportale regionale con i poligoni comunali...")

    # gli attributi da entrambi i GeodataFrame vengono mantenuti
    edif_reg_filt = gpd.overlay(edif_reg, adm, how="intersection")

    log.info(f"l'intersezione è andata a buon fine")
except Exception as e:
    log.error(f"è impossibile incrociare gli edifici dal Geoportale regionale con i poligoni comunali: {e}")
    raise SystemExit(1)

# Trasformazione degli attributi
try:
    log.info(f"è iniziata la trasformazione degli attributi...")

    # Geoportale regionale
    edif_reg_filt["anno"] = None  # perché l'anno di costruzione è sconosciuto
    edif_reg_filt["fonte"] = "modello digitale della superficie"

    # riclassificare il tipo di uso
    log.info(f"riclassifico il tipo di uso per 4 comuni...")
    cond_resid = ["01", "0102"]
    cond_ind = ["06", "07", "08", "0802"]
    cond_pa = ["02", "03"]

    edif_reg_filt["tipo"] = np.where(
            edif_reg_filt["edi_uso"].isin(cond_resid),
            "residenziale",
            (np.where(
                    edif_reg_filt["edi_uso"].isin(cond_ind),
                    "comm./ind./trasp.",
                    np.where(
                            edif_reg_filt["edi_uso"].isin(cond_pa),
                            "PA",
                            "altro")))
    )

    edif_reg_filt.rename(columns={"id": "orig_id"}, inplace=True)
    edif_reg_filt = edif_reg_filt[["orig_id", "tipo", "comune", "anno", "fonte", "geometry"]]

    log.info(f"trasformo anno di costruzione per Vicenza...")
    edif_vi["fonte"] = "modello digitale della superficie"
    edif_vi["Anni_epoca"].apply(str)
    edif_vi["anno"] = None
    edif_vi["anno"] = np.where(
            edif_vi["Anni_epoca"].str.isdigit(),
            pd.to_numeric(
                    edif_vi["Anni_epoca"],
                    errors="coerce",
                    downcast="integer"),
            None)

    log.info(f"riclassifico il tipo di uso per Vicenza...")

    cond_resid = ["residenziale", "residenziale garage", "residenziale rimessa"]
    cond_ind = ["commerciale", "industriale", "produttivo",
                "magazzino locale di deposito", "parcheggi"]
    cond_pa = ["amministrazione pubblica", "direzionale"]

    edif_vi["tipo"] = np.where(
            edif_vi["Uso"].isin(cond_resid),
            "residenziale",
            (np.where(
                    edif_vi["Uso"].isin(cond_ind),
                    "comm./ind./trasp.",
                    (np.where(
                            edif_vi["Uso"].isin(cond_pa),
                            "PA",
                            "altro"))
            ))
    )

    edif_vi.rename(columns={"gid": "orig_id", }, inplace=True)
    edif_vi["comune"] = "Vicenza"
    edif_vi = edif_vi[["orig_id", "tipo", "comune", "anno", "geometry"]]

    edifici_uniti = gpd.GeoDataFrame(
        pd.concat([edif_vi, edif_reg_filt], ignore_index=True),
        crs=edif_vi.crs)

    # aggiungere un nuovo campo con l'area totale della proiezione a terra
    edifici_uniti["proiezione_mq"] = edifici_uniti["geometry"].area
    log.info(f"la trasformazione degli attributi di edifici è andata a buon fine ")

    # creare un Overlap con la maschera NoData
    nodata_ed_uniti = gpd.overlay(edifici_uniti, nodata_mask, how="intersection")
    nodata_ed_uniti_ids = nodata_ed_uniti["orig_id"].tolist()

except Exception as e:
    log.error(f"è impossibile trasformare gli attributi di edifici: {e}")
    raise SystemExit(1)

# Salvare il risultato
try:
    edifici_uniti_name = f"..\data\output\edifici_uniti.json"
    edifici_uniti.to_file(edifici_uniti_name, driver="GeoJSON")
    log.info(f"il file '{edifici_uniti_name}' è salvato")
except Exception as e:
    log.error(f"è impossibile salvare il risultato finale: {e}")
    raise SystemExit(1)


log.info(f"STEP 3. PREPARAZIONE DATI RASTER")

if cfg.SKIP_RASTER:
    log.warning("elaborazione del raster è disattivato")
    ins_file = latest_file("..\data\output", "insolazione_filtrato.tif")
    if Path(ins_file).is_file():
        log.info(f"viene usato '{ins_file}'")
    else:
        log.error(f"non c'è nessun RASTER filtrato dell'insolazione: controlla la cartella '..\data\output' e nomi di file")
        raise SystemExit(1)
else:
    log.warning("raster filtrato con insolazione sarà sovrascritto")
    try:
        # aprire i file raster in Read mode
        insol_ = rst.open(cfg.INSOLAZIONE)
        affine = insol_.transform
        insol = insol_.read(1)
        pend = rst.open(cfg.PENDENZA).read(1)
        espos = rst.open(cfg.ESPOSIZIONE).read(1)

        log.info(f"i file raster sono letti")

        log.info(f"eseguo Map Algebra - mascheratura di valori raster...")
        insol_f = np.where(
                (np.greater_equal(insol, cfg.MIN_INS)
                 & np.less_equal(pend, cfg.MAX_PEND)
                 & np.greater_equal(espos, cfg.MIN_ESP)
                 & np.less_equal(espos, cfg.MAX_ESP)
                 ),
                insol,
                cfg.NODATA)
        log.info(f"l'insolazione irrelevante è stata filtrata")

    except Exception as e:
        log.error(f"è impossibile elaborare i dati raster: {e}")
        raise SystemExit(1)

    log.info(f"insolazione irrelevante è stata filtrata")

    log.info(f"eseguo salvataggio dell'insolazione elaborata")
    try:
        with rst.open(
                f"..\data/output/insolazione_filtrato.tif",
                "w",
                driver="GTiff",
                height=insol_f.shape[0],
                width=insol_f.shape[1],
                count=1,
                dtype=insol_f.dtype,
                crs=insol_.crs,
                transform=affine
        ) as dst:
            dst.write_band(1, insol_f)
        ins_file = latest_file("..\data\output", "insolazione_filtrato.tif")
    except Exception as e:
        log.error(f"è impossibile salvare il raster elaborato: {e}")
        raise SystemExit(1)

log.info(f"STEP 4. STATISTICHE ZONALI")

try:
    log.info("apro i file raster...")
    insol_f_ = rst.open(ins_file)
    affine = insol_f_.transform
    insol_f = insol_f_.read(1)

    # estrarre l'area di un pixel, in metri quadri
    pixel_size_x, pixel_size_y = insol_f_.res
    pixel_area = pixel_size_x * pixel_size_y

    log.info("calcolo le statistiche...")

    edifici_stats = get_zonal_stats(edifici_uniti, insol_f, ["count", "mean"], cfg.NODATA, affine)

    # creare un nuovo campo con l'area insolata, in metri quadri
    edifici_stats["area_ins"] = edifici_stats["count"] * pixel_area

    # selezionare solo edifici che superano il limite minimo dell'area insolata
    edifici_stats = edifici_stats[edifici_stats["area_ins"] >= cfg.MIN_INS_AREA]

    # creare un nuovo campo con l'energia annuale totale solo per le superficie utilizzabili, megawatt-ora annui
    edifici_stats["sup_util_mwh"] = edifici_stats["count"] * edifici_stats["mean"] / 1000

    # conversione della radiazione solare in energia producibile, megawatt-ora annui
    edifici_stats["elett_prod_mwh"] = edifici_stats["sup_util_mwh"] * cfg.EFF * cfg.PR

    log.info("ri-elaborazione delle statistiche secondo la formula empirica")

    nodata_ed_stats = gpd.overlay(edifici_stats, nodata_mask, how="intersection")
    nodata_ed_stats_ids = nodata_ed_stats["orig_id"].tolist()

    nodata_ed_uniti_ids = [x for x in nodata_ed_uniti_ids if x not in nodata_ed_stats_ids]

    edifici_uniti = edifici_uniti[edifici_uniti["proiezione_mq"] >= cfg.MIN_INS_AREA]

    edifici_stats = edifici_stats.append(
            edifici_uniti[edifici_uniti["orig_id"].isin(nodata_ed_uniti_ids)],
            ignore_index=True)

    nodata_ed_ids = nodata_ed_stats_ids + nodata_ed_uniti_ids
    edifici_stats["fonte"] = np.where(
            edifici_stats["orig_id"].isin(nodata_ed_ids),
            "formula empirica",
            edifici_stats["fonte"])
    edifici_stats["fonte"] = np.where(
            edifici_stats["anno"] >= 2016,
            "formula empirica",
            edifici_stats["fonte"])

    edifici_stats.loc[edifici_stats["fonte"] == "formula empirica", "mean"] = None
    edifici_stats.loc[edifici_stats["fonte"] == "formula empirica", "count"] = None
    edifici_stats.loc[edifici_stats["fonte"] == "formula empirica", "area_ins"] = None
    edifici_stats.loc[edifici_stats["fonte"] == "formula empirica", "sup_util_mwh"] = None
    edifici_stats.loc[edifici_stats["fonte"] == "formula empirica", "elett_prod_mwh"] = None

    edifici_stats["_temp"] = 0.104 * edifici_stats["proiezione_mq"] - 6.84

    edifici_stats.loc[edifici_stats["fonte"] == "formula empirica", "elett_prod_mwh"] = edifici_stats["_temp"]


    # edifici_stats["elett_prod_mwh"] = np.where(
    #         edifici_stats["fonte"].equals("formula empirica"),
    #         edifici_stats["_temp"],
    #         edifici_stats["elett_prod_mwh"])

    del edifici_stats["_temp"]
    log.info("le statistiche sono calcolate")

except Exception as e:
    log.error(f"è impossibile calcolare le statistiche zonali per gli edifici uniti: {e}")
    raise SystemExit(1)

try:
    log.warning("edifici con le statistiche saranno sovrascritti")
    edifici_stats_name_json = f"..\data\output\edifici_stats.json"
    edifici_stats.to_file(edifici_stats_name_json, driver="GeoJSON")
    log.info(f"il risultato finale è salvato come '{edifici_stats_name_json}'")

    edifici_stats_name_js = f"..\webmap\layers\edifici.js"
    edifici_stats.to_crs(4326).to_file(edifici_stats_name_js, driver="GeoJSON")
    with open(edifici_stats_name_js, "r+") as f:
        content = f.read()
        f.seek(0, 0)
        f.write("var edifici = " + content + ";")
    log.info(f"il file '{edifici_stats_name_js}' della mappa web è aggiornato")


except Exception as e:
    log.error(f"è impossibile salvare il risultato finale: {e}")
    raise SystemExit(1)

log.critical("L'ESECUZIONE È FINITA CON SUCCESSO")
