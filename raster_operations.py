"""
Author: Resul Emre AYGAN
"""

from osgeo.gdal import Translate, Warp, GDT_Byte, GDT_UInt16, GRA_Bilinear


def crop_raster_with_translate(raster_path, output_path, res_x, res_y, output_bounds, raster_format, raster_bit=8):
    try:
        if raster_bit == 16:
            raster_type = GDT_UInt16
        else:
            raster_type = GDT_Byte

        temp_ds = Translate(output_path, raster_path, projWin=output_bounds,
                            xRes=res_x, yRes=-res_y, outputType=raster_type, format=raster_format)
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
