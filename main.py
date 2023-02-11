"""
Author: Resul Emre AYGAN
"""

import os
import sys
import json
from osgeo import gdal, ogr, osr
import numpy as np
import math
import matplotlib.pyplot as plt
from uuid import uuid4

from osr import OAMS_TRADITIONAL_GIS_ORDER
from osgeo.gdal import __version__ as osgeo_version
from shapely import wkt
from shapely.geometry import Polygon, MultiPolygon


def get_array_from_raster(file_path, only_info=True):
    temp_ds = gdal.Open(file_path)

    band_number = temp_ds.RasterCount
    projection = temp_ds.GetProjection()
    geo_transform = temp_ds.GetGeoTransform()

    width = temp_ds.RasterXSize
    height = temp_ds.RasterYSize

    min_x = geo_transform[0]
    min_y = geo_transform[3] + width * geo_transform[4] + height * geo_transform[5]
    max_x = geo_transform[0] + width * geo_transform[1] + height * geo_transform[2]
    max_y = geo_transform[3]

    res_x = geo_transform[1]
    res_y = geo_transform[5]

    lon = [min_x, max_x, max_x, min_x]  # [ulx, lrx, lrx, ulx]
    lat = [max_y, max_y, min_y, min_y]  # [uly, uly, lry, lry]

    utm_sr = osr.SpatialReference(wkt=projection)
    epsg = int(utm_sr.GetAttrValue('AUTHORITY', 1))

    geom_str = "POLYGON (("
    for index in range(len(lon)):
        geom_str += str(lon[index]) + " " + str(lat[index]) + ","
    geom_str += str(lon[0]) + " " + str(lat[0]) + " ))"

    geom_poly = wkt.loads(geom_str)

    alpha_channel = None

    if not only_info:
        if band_number > 2:
            original_raster = np.dstack([temp_ds.GetRasterBand(1).ReadAsArray(),
                                         temp_ds.GetRasterBand(2).ReadAsArray(),
                                         temp_ds.GetRasterBand(3).ReadAsArray()])
            if band_number > 3:
                alpha_channel = temp_ds.GetRasterBand(temp_ds.RasterCount).ReadAsArray().astype(np.uint8)
        else:
            original_raster = np.dstack([temp_ds.GetRasterBand(1).ReadAsArray()])

            if band_number == 2:
                alpha_channel = temp_ds.GetRasterBand(temp_ds.RasterCount).ReadAsArray().astype(np.uint8)

        temp_ds = None

        return original_raster, alpha_channel, geo_transform, min_x, max_y, res_x, res_y, width, height, epsg, geom_poly
    else:
        temp_ds = None

        return geo_transform, min_x, max_y, res_x, res_y, width, height, epsg, geom_poly


def crop_raster_with_translate(raster_path, output_path, res_x, res_y, output_bounds, raster_format):
    try:
        temp_ds = gdal.Translate(output_path, raster_path, projWin=output_bounds,
                                 xRes=res_x, yRes=-res_y, outputType=gdal.gdalconst.GDT_Byte, format=raster_format)
        temp_ds = None
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

        _ = gdal.Warp(output_path, raster_path, width=width, height=height, dstSRS=epsg_str,
                      cutlineDSName=shape_path, cropToCutline=cutline_bool, outputBounds=output_bounds,
                      resampleAlg=gdal.GRA_Bilinear, dstAlpha=(not alpha_info),
                      warpOptions=wo_string, multithread=multi)
        _ = None

        return output_path

    except Exception as error:
        print(f"Raster kesme metotunda hata olustu: {error} - {raster_path}")


def transform_polygon_osr(polygon, src_epsg=4326, dst_epsg=3857):
    try:
        if isinstance(polygon, Polygon) or isinstance(polygon, MultiPolygon):
            polygon = ogr.CreateGeometryFromWkt(polygon.wkt)

        if not isinstance(polygon, ogr.Geometry):
            print("Geometri ogr geometri formatinda degil!")
            return False

        src = osr.SpatialReference()
        tgt = osr.SpatialReference()

        src.ImportFromEPSG(src_epsg)
        tgt.ImportFromEPSG(dst_epsg)

        if int(osgeo_version[0]) >= 3:
            # GDAL 3 changes axis order: https://github.com/OSGeo/gdal/issues/1546
            src.SetAxisMappingStrategy(OAMS_TRADITIONAL_GIS_ORDER)
            tgt.SetAxisMappingStrategy(OAMS_TRADITIONAL_GIS_ORDER)

        transformer = osr.CoordinateTransformation(src, tgt)

        polygon.Transform(transformer)

        return wkt.loads(polygon.ExportToWkt())

    except Exception as error:
        print(f"transform_polygon_osr isleminde hata olustu: {error}")


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

    if alpha_channel is None or generate_alpha:
        if raster_array.shape[-1] == 3:
            alpha_channel = ((raster_array[:, :, 0] > 0) | (raster_array[:, :, 1] > 0) | (raster_array[:, :, 2] > 0)) \
                            * np.uint8(255)
            result_array = np.dstack([result_array[:, :, 0], result_array[:, :, 1], result_array[:, :, 2],
                                      alpha_channel])
        else:
            alpha_channel = raster_array[:, :, 0].copy()
            result_array = np.dstack([result_array[:, :, 0], result_array[:, :, 0], result_array[:, :, 0],
                                      alpha_channel])

    plt.imsave(output_path, result_array, format='png')

    return output_path


def bounds_to_polygon(geom_bounds):
    return Polygon([(geom_bounds[0], geom_bounds[1]), (geom_bounds[0], geom_bounds[3]),
                    (geom_bounds[2], geom_bounds[3]), (geom_bounds[2], geom_bounds[1])])


if __name__ == '__main__':
    if not os.path.exists("config.json"):
        print("Konfig dosyasi bulunamadi!\n")
        sys.exit()

    with open("config.json") as json_data_file:
        data = json.load(json_data_file)

    save_as_png = data["save_as_png"]
    output_dir = data["output_dir"]
    crop_size_x = data["crop_size_x"]
    crop_size_y = data["crop_size_y"]

    use_warp = False
    raster_format = data["raster_format"]

    raster_path = data["raster_path"]

    raster_path_4326 = os.path.join(os.path.split(raster_path)[0], str(uuid4()) + '.tif')

    [geo_transform, x_min, y_max, res_x, res_y, width, height, epsg, geom_poly] = get_array_from_raster(
        file_path=raster_path)

    generate_alpha = False

    if epsg != 4326:
        generate_alpha = True
        gdal.Warp(raster_path_4326, raster_path, srcSRS="EPSG:" + str(epsg), dstSRS="EPSG:4326", dstAlpha=True)

        [geo_transform, x_min, y_max, res_x, res_y, width, height, epsg, geom_poly] = get_array_from_raster(
            file_path=raster_path_4326)
        raster_path = raster_path_4326

    x_not_round = width / crop_size_x
    x_round = math.ceil(x_not_round)
    y_not_round = height / crop_size_y
    y_round = math.ceil(y_not_round)

    pix_to_mx = crop_size_x * x_round * res_x
    pix_to_my = crop_size_y * y_round * abs(res_y)

    x_size = pix_to_mx / x_round
    y_size = pix_to_my / y_round

    x_steps = [x_min + x_size * i for i in range(x_round + 1)]
    y_steps = [y_max - y_size * i for i in range(y_round + 1)]

    for i in range(x_round):
        for j in range(y_round):
            temp_x_min = x_steps[i]
            temp_x_max = x_steps[i + 1]
            temp_y_max = y_steps[j]
            temp_y_min = y_steps[j + 1]

            temp_output_path = os.path.join(output_dir, (str("01") + "-" + str(j) + "-" + str(i) + ".tif"))
            temp_output_path_png = os.path.join(output_dir, (str("01") + "-" + str(j) + "-" + str(i) + ".png"))

            temp_bounds = (abs(temp_x_min), abs(temp_y_max), abs(temp_x_max), abs(temp_y_min))

            if use_warp:
                temp_polygon = bounds_to_polygon(geom_bounds=temp_bounds)
                transformed_poly = transform_polygon_osr(polygon=temp_polygon, src_epsg=epsg, dst_epsg=4326)
                temp_bounds = transformed_poly.bounds

                _ = crop_raster_with_warp(raster_path=raster_path, output_bounds=temp_bounds,
                                          output_path=temp_output_path, epsg_number=4326, multi=True, num_thread=-9999)
            else:
                crop_raster_with_translate(raster_path=raster_path, output_path=temp_output_path,
                                           res_x=res_x, res_y=res_y, output_bounds=temp_bounds,
                                           raster_format=raster_format)

            [original_raster, alpha_channel, geo_transform, min_x, max_y, res_x, res_y, width, height,
             epsg, geom_poly] = get_array_from_raster(file_path=temp_output_path, only_info=False)

            if save_as_png:
                save_raster_as_png(raster_array=original_raster, alpha_channel=alpha_channel,
                                   output_path=temp_output_path_png, generate_alpha=generate_alpha)
    ds = None

    if os.path.exists(raster_path_4326):
        os.remove(raster_path_4326)
