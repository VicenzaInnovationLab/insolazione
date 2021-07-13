# || INTERROGAZIONE DEL GEOPORTALE REGIONALE

SKIP_DOWNLOAD = True  # metti 'True' se gli edifici dal Geoportale sono già scaricati in 'processing/download'

ENDPOINT_REG = "http://idt2-geoserver.regione.veneto.it:80/geoserver/wfs"
EDIFLAYER = "edifici_veneto_apr2021"
SRSNAME ="EPSG:6876"
BBOX = f"2952786, 5036043, 2974090, 5055053, {SRSNAME}"  # copre tutti e cinque comuni del progetto


# || RASTER

SKIP_RASTER = True  # metti 'True' se non vuoi eseguire lo calcolo su dati raster (lo step 3)

INSOLAZIONE = r"../data/insolazione.tif"
MIN_INS = 800  # in kW*h/m2 annui; saranno eliminati tutti i valori minori
NODATA = -9999

ESPOSIZIONE = r"../data/esposizione.tif"
MIN_ESP, MAX_ESP = 22.5, 337.5  # in gradi; saranno eliminati tutti i valori fuori da questo range

PENDENZA = r"../data/pendenza.tif"
MAX_PEND = 45  # in gradi; saranno eliminati tutti i valori maggiori

MIN_INS_AREA = 30  # in m2; min area di superficie adatta per l'installazione di pannelli solari

EFF = 0.15  # efficienza del pannello che è in grado di convertire solo una parte dell'energia solare in entrata
PR = 0.86  # performance ratio: la parte dell'elettricità che viene mantenuta nell'installazione

# || LOGGING

# Dimensione massima di un logfile in megabyte
LOG_SIZE = 1

# Livello del log: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL = "DEBUG"

# Il numero di file di log creati quando viene superata la dimensione massima del logging
BACKUP_COUNT = 2

# Directory dei log
LOG_DIR = "log"

# Formato della voce di log
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"
