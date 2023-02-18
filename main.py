"""
Author: Resul Emre AYGAN
"""

from sys import exit
from osgeo import gdal
import numpy as np
from math import ceil
import matplotlib.pyplot as plt

from utils.load_params import load_config
from geometry_operations import bounds_to_polygon, transform_polygon_osr, check_epsg, lon_lat_to_geom, \
    create_shapefile, clip_shapefile_with_shapefile
from raster_operations import crop_raster_with_warp, crop_raster_with_translate, change_raster_projection, \
    vector_rasterization
from utils.file_operations import delete_file, file_exists, get_file_name, generate_temp_file_path


def get_array_from_raster(file_path, only_info=True):
    raster_ds = gdal.Open(file_path)

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


if __name__ == '__main__':
    [save_as_png, output_dir, crop_size_x, crop_size_y, crop_shape, shape_path, raster_format, raster_path,
     seg_mask, seg_mask_as_png, convert_coco] = load_config()
    use_warp = False

    if not file_exists(file_path=raster_path):
        print(f"Raster bulunamadi! - {raster_path}")
        exit()

    raster_name = get_file_name(file_path=raster_path)
    raster_path_4326 = generate_temp_file_path(output_path=output_dir, file_ext='tif')
    annotations_path = generate_temp_file_path(output_path=output_dir,
                                               file_ext='json',
                                               file_name=raster_name.split('.')[0] + '_annotations')

    [geo_transform, x_min, y_max, res_x, res_y, width, height, epsg, geom_poly] = get_array_from_raster(
        file_path=raster_path)
    #
    # crop_size_x = min(width, crop_size_x)
    # crop_size_y = min(height, crop_size_x)

    generate_alpha = False

    if epsg != 4326:
        print(f"Raster EPSG:4326 formatinda degil, donusturuluyor. - {raster_path}")
        generate_alpha = True

        if not change_raster_projection(raster_path=raster_path, output_path=raster_path_4326, src_epsg=epsg,
                                        dst_epsg=4326):
            exit()

        [geo_transform, x_min, y_max, res_x, res_y, width, height, epsg, geom_poly] = get_array_from_raster(
            file_path=raster_path_4326)
        raster_path = raster_path_4326

    x_not_round = width / crop_size_x
    x_round = ceil(x_not_round)
    y_not_round = height / crop_size_y
    y_round = ceil(y_not_round)

    pix_to_mx = crop_size_x * x_round * res_x
    pix_to_my = crop_size_y * y_round * abs(res_y)

    x_size = pix_to_mx / x_round
    y_size = pix_to_my / y_round

    x_steps = [x_min + x_size * i for i in range(x_round + 1)]
    y_steps = [y_max - y_size * i for i in range(y_round + 1)]

    if crop_shape:
        if not file_exists(file_path=shape_path):
            print(f"Shapefile bulunamadi! - {shape_path}")
            crop_shape = False

    image_list = []
    seg_list = []

    for i in range(x_round):
        for j in range(y_round):
            temp_x_min = x_steps[i]
            temp_x_max = x_steps[i + 1]
            temp_y_max = y_steps[j]
            temp_y_min = y_steps[j + 1]

            temp_file_name = str("01") + "-" + str(j) + "-" + str(i)
            temp_output_path = generate_temp_file_path(output_path=output_dir, file_name=temp_file_name, file_ext='tif')
            temp_output_path_png = generate_temp_file_path(output_path=output_dir,
                                                           file_name=temp_file_name,
                                                           file_ext='png')

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
                image_list.append(temp_output_path_png)
            else:
                image_list.append(temp_output_path)

            if crop_shape:
                temp_shape_path = generate_temp_file_path(output_path=output_dir,
                                                          file_name=temp_file_name + "_tmp",
                                                          file_ext='shp')
                temp_shx_path = generate_temp_file_path(output_path=output_dir,
                                                        file_name=temp_file_name + "_tmp",
                                                        file_ext='shx')
                temp_dbf_path = generate_temp_file_path(output_path=output_dir,
                                                        file_name=temp_file_name + "_tmp",
                                                        file_ext='dbf')
                temp_prj_path = generate_temp_file_path(output_path=output_dir,
                                                        file_name=temp_file_name + "_tmp",
                                                        file_ext='prj')
                temp_cfg_path = generate_temp_file_path(output_path=output_dir,
                                                        file_name=temp_file_name + "_tmp",
                                                        file_ext='cfg')
                crop_shape_path = generate_temp_file_path(output_path=output_dir,
                                                          file_name=temp_file_name,
                                                          file_ext='shp')

                if create_shapefile(geom_wkt=geom_poly.wkt, output_path=temp_shape_path, epsg=epsg):
                    if not clip_shapefile_with_shapefile(input_shapefile=shape_path, clip_shapefile=temp_shape_path,
                                                         output_shapefile=crop_shape_path):
                        delete_file(file_path=crop_shape_path)

                delete_file(file_path=temp_shape_path)
                delete_file(file_path=temp_shx_path)
                delete_file(file_path=temp_dbf_path)
                delete_file(file_path=temp_prj_path)
                delete_file(file_path=temp_cfg_path)

                if seg_mask:
                    seg_mask_path = generate_temp_file_path(output_path=output_dir,
                                                            file_name=temp_file_name + "_seg",
                                                            file_ext='tif')

                    temp_mask_bounds = (abs(temp_x_min), abs(temp_y_min), abs(temp_x_max), abs(temp_y_max))

                    vector_rasterization(shape_path=crop_shape_path, output_bounds=temp_mask_bounds,
                                         output_path=seg_mask_path, res_x=res_x, res_y=res_y)

                    if seg_mask_as_png:
                        seg_mask_png_path = generate_temp_file_path(output_path=output_dir,
                                                                    file_name=temp_file_name + "_seg",
                                                                    file_ext='png')

                        [_original_raster, _alpha_channel, _geo_transform, _min_x, _max_y, _res_x, _res_y, _width,
                         _height,
                         _epsg, _geom_poly] = get_array_from_raster(file_path=seg_mask_path, only_info=False)

                        save_raster_as_png(raster_array=_original_raster, output_path=seg_mask_png_path,
                                           generate_alpha=False)

                        seg_list.append(seg_mask_png_path)
                    else:
                        seg_list.append(seg_mask_path)

    ds = None

    delete_file(file_path=raster_path_4326)
