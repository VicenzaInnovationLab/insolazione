import rasterio
import config as cfg
from datetime import datetime as dt
import numpy as np

now_str = dt.now().strftime("%Y%m%d-%H%M%S")  # il marcatempo per aggiungere nei nomi di file


# aprire i file raster in Read mode
insol_ = rasterio.open(cfg.INSOLAZIONE)
insol = insol_.read(1)
pend = rasterio.open(cfg.PENDENZA).read(1)
espos = rasterio.open(cfg.ESPOSIZIONE).read(1)

# estrarre l'area di un pixel, in metri quadri
pixel_size_x, pixel_size_y = insol_.res
pixel_area = pixel_size_x * pixel_size_y
print(pixel_size_x, pixel_size_y, pixel_area)

# map algebra
insol_f = np.where(
        (np.greater_equal(insol, cfg.MIN_INS)
         & np.less_equal(pend, cfg.MAX_PEND)
         & np.greater_equal(espos, cfg.MIN_ESP)
         & np.less_equal(espos, cfg.MAX_ESP)
         ),
        insol,
        -9999)

with rasterio.open(
        f"processing/output/insolazione_filtrata.tif",
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
