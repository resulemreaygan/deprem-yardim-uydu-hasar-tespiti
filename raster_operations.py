"""
Author: Resul Emre AYGAN
"""

from osgeo.gdal import Open, Translate, Warp, GDT_Byte, GDT_UInt16, GRA_Bilinear, Rasterize
import numpy as np
from geometry_operations import check_epsg, lon_lat_to_geom
import matplotlib.pyplot as plt


def crop_raster_with_translate(raster_path, output_path, res_x, res_y, output_bounds, raster_format, raster_bit=8):
    try:
        if raster_bit == 16:
            raster_type = GDT_UInt16
        else:
            raster_type = GDT_Byte

        _ = Translate(output_path, raster_path, projWin=output_bounds, xRes=res_x, yRes=-res_y,
                      outputType=raster_type, format=raster_format)
        _ = None
    except Exception as error:
        print(f"Raster kesme metotunda hata olustu: {error} - {raster_path}")


def crop_raster_with_warp(raster_path, shape_path=None, output_bounds=None, alpha_info=False, output_path=None,
                          width=0, height=0, cutline_bool=False, epsg_number=4326, multi=False, num_thread=1):
    try:
        wo_string = []

        if epsg_number == 4326:
            epsg_str = "EPSG:4326"
        else:
            epsg_str = "EPSG:3857"

        if shape_path is not None:
            wo_string.append("CUTLINE_ALL_TOUCHED=TRUE")

        if num_thread != 1:
            wo_string.append("NUM_THREADS=ALL_CPUS")

        _ = Warp(output_path, raster_path, width=width, height=height, dstSRS=epsg_str,
                 cutlineDSName=shape_path, cropToCutline=cutline_bool, outputBounds=output_bounds,
                 resampleAlg=GRA_Bilinear, dstAlpha=(not alpha_info),
                 warpOptions=wo_string, multithread=multi)
        _ = None

        return output_path

    except Exception as error:
        print(f"Raster kesme metotunda hata olustu: {error} - {raster_path}")


def change_raster_projection(raster_path, output_path, src_epsg="EPSG:3857", dst_epsg="EPSG:4326", dst_alpha=True):
    try:
        src_epsg = "EPSG:" + str(src_epsg)
        dst_epsg = "EPSG:" + str(dst_epsg)

        _ = Warp(output_path, raster_path, srcSRS=src_epsg, dstSRS=dst_epsg, dstAlpha=dst_alpha)
        _ = None

        return True
    except Exception as error:
        print(f"Projeksiyon degistirme isleminde hata olustu. - Hata: {error}")
        return False


def vector_rasterization(shape_path, output_path, output_bounds, res_x, res_y, burn_value=255,
                         output_bit=GDT_Byte):
    try:
        # if output_bounds is None:
        #     ds_shp = ogr.Open(shape_path)
        #     shp_layer = ds_shp.GetLayer()
        #     minx, maxx, miny, maxy = shp_layer.GetExtent()
        #     output_bounds = [minx, miny, maxx, maxy]

        _ = Rasterize(output_path, shape_path, xRes=res_x, yRes=-res_y, burnValues=burn_value,
                      outputBounds=output_bounds, outputType=output_bit, outputSRS="EPSG:4326")
        _ = None

        return True
    except Exception as error:
        print(f"Vektorden raster uretilirken hata olustu: {error}")
        return False


def get_array_from_raster(file_path, only_info=True):
    raster_ds = Open(file_path)

    if raster_ds is None:
        raise IOError(f'Tif dosyasi acilamadi! {file_path}')

    band_number = raster_ds.RasterCount
    projection = raster_ds.GetProjection()
    geo_transform = raster_ds.GetGeoTransform()

    width = raster_ds.RasterXSize
    height = raster_ds.RasterYSize

    min_x = geo_transform[0]
    min_y = geo_transform[3] + width * geo_transform[4] + height * geo_transform[5]
    max_x = geo_transform[0] + width * geo_transform[1] + height * geo_transform[2]
    max_y = geo_transform[3]

    res_x = geo_transform[1]
    res_y = geo_transform[5]

    lon = [min_x, max_x, max_x, min_x]  # [ulx, lrx, lrx, ulx]
    lat = [max_y, max_y, min_y, min_y]  # [uly, uly, lry, lry]

    epsg = check_epsg(projection=projection)

    geom_poly = lon_lat_to_geom(lon=lon, lat=lat)

    alpha_channel = None

    if not only_info:
        if band_number > 2:
            original_raster = np.dstack([raster_ds.GetRasterBand(1).ReadAsArray(),
                                         raster_ds.GetRasterBand(2).ReadAsArray(),
                                         raster_ds.GetRasterBand(3).ReadAsArray()])
            if band_number > 3:
                alpha_channel = raster_ds.GetRasterBand(raster_ds.RasterCount).ReadAsArray().astype(np.uint8)
        else:
            original_raster = np.dstack([raster_ds.GetRasterBand(1).ReadAsArray()])

            if band_number == 2:
                alpha_channel = raster_ds.GetRasterBand(raster_ds.RasterCount).ReadAsArray().astype(np.uint8)

        temp_ds = None

        return original_raster, alpha_channel, geo_transform, min_x, max_y, res_x, res_y, width, height, epsg, geom_poly
    else:
        temp_ds = None

        return geo_transform, min_x, max_y, res_x, res_y, width, height, epsg, geom_poly


def normalize_byte(raster_array):
    info = np.iinfo(raster_array.dtype)
    raster_array = raster_array.astype(np.float32) / info.max
    raster_array = 255 * raster_array

    return raster_array.astype(np.uint8)


def save_raster_as_png(raster_array, output_path, generate_alpha, normalize=True, alpha_channel=None):
    if normalize:
        result_array = normalize_byte(raster_array=raster_array)
    else:
        result_array = raster_array.copy()

    if generate_alpha:
        if raster_array.shape[-1] == 3:
            if alpha_channel is None:
                alpha_channel = ((raster_array[:, :, 0] > 0) | (raster_array[:, :, 1] > 0) |
                                 (raster_array[:, :, 2] > 0)) * np.uint8(255)
            result_array = np.dstack([result_array[:, :, 0], result_array[:, :, 1], result_array[:, :, 2],
                                      alpha_channel])
        else:
            if alpha_channel is None:
                alpha_channel = raster_array[:, :, 0].copy()
            result_array = np.dstack([result_array[:, :, 0], result_array[:, :, 0], result_array[:, :, 0],
                                      alpha_channel])

    if raster_array.shape[-1] == 1:
        result_array = np.dstack([result_array[:, :, 0], result_array[:, :, 0], result_array[:, :, 0]])

    plt.imsave(output_path, result_array, format='png')

    return output_path
