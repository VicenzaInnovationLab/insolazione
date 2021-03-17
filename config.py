# INTERROGAZIONE DEL GEOPORTALE REGIONALE
ENDPOINT_REG = "http://idt2-geoserver.regione.veneto.it:80/geoserver/wfs"
LAYER = "edifici_veneto_6876"
SRSNAME ="EPSG:6876"
BBOX = f"2952786, 5036043, 2974090, 5055053, {SRSNAME}"  # copre tutti e cinque comuni contermini
DOWNLOAD = True  # False se gli edifici dal Geoportale regionale sono già scaricati in './download'

# SIT VI
EDIF_VI = "edifici_sitvi_7795"  # il nome dello Shapefile dal SIT VI (senza l'estensione)
ADM_VI = "cinque_comuni_7795"  # il nome dello JSON con i limiti amministrativi (senza l'estensione)


# LOG
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
