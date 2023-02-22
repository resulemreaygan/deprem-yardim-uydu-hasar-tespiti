"""
Author: Resul Emre AYGAN
"""

from sys import exit
from math import ceil
from datetime import datetime

from utils.load_params import load_config
from geometry_operations import bounds_to_polygon, transform_polygon_osr, create_shapefile, \
    clip_shapefile_with_shapefile, get_categories_from_shapefile, read_shapefile_with_gpd, save_gdf_to_shapefile
from raster_operations import crop_raster_with_warp, crop_raster_with_translate, change_raster_projection, \
    vector_rasterization, get_array_from_raster, save_raster_as_png
from coco_operations import start_conversion_coco, check_categories, model_class
from utils.file_operations import write_json, delete_file, file_exists, get_file_name, generate_temp_file_path

if __name__ == '__main__':
    print(f'Islem basladi - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

    [save_as_png, output_dir, crop_size_x, crop_size_y, crop_shape, shape_path, raster_format, raster_path,
     seg_mask, seg_mask_as_png, convert_coco, _visualize_coco, _annotations_path,
     _annotations_image_path, _drawn_annotations_path] = load_config()
    use_warp = False

    unique_categories = get_categories_from_shapefile(shapefile_path=shape_path)
    categories_dict = check_categories(categories=unique_categories)

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
    categories_seg_list = []

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

                added_seg_list = False

                if seg_mask:
                    seg_mask_path = generate_temp_file_path(output_path=output_dir,
                                                            file_name=temp_file_name + "_seg",
                                                            file_ext='tif')

                    temp_mask_bounds = (abs(temp_x_min), abs(temp_y_min), abs(temp_x_max), abs(temp_y_max))

                    vector_rasterization(shape_path=crop_shape_path, output_bounds=temp_mask_bounds,
                                         output_path=seg_mask_path, res_x=res_x, res_y=res_y)

                    if not len(categories_dict) == 1 and 'buildings' in categories_dict.keys():
                        data = read_shapefile_with_gpd(shapefile_path=crop_shape_path)

                        if 'damage_gra' in data.keys():
                            for damage_gra_val in data['damage_gra'].unique():
                                uncertain_case = False

                                if damage_gra_val not in model_class.keys():
                                    file_val = model_class[""]
                                else:
                                    file_val = model_class[damage_gra_val]

                                categories_shape_path = generate_temp_file_path(
                                    output_path=output_dir, file_name=f'{temp_file_name}_{file_val}',
                                    file_ext='shp')

                                if "Possibly damaged" == damage_gra_val or "Damaged" == damage_gra_val:
                                    if file_exists(file_path=categories_shape_path):
                                        continue
                                    else:
                                        uncertain_case = True

                                categories_mask_path = generate_temp_file_path(
                                    output_path=output_dir, file_name=f'{temp_file_name}_{file_val}_seg',
                                    file_ext='tif')
                                categories_mask_png_path = generate_temp_file_path(
                                    output_path=output_dir, file_name=f'{temp_file_name}_{file_val}_seg',
                                    file_ext='png')

                                print(f'Kategorinin shapefile dosyasi olusturuluyor. {categories_shape_path} - '
                                      f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

                                if uncertain_case:
                                    filtered_data = data[(data['damage_gra'] == "Possibly damaged") |
                                                         (data['damage_gra'] == "Damaged")]
                                else:
                                    filtered_data = data[data['damage_gra'] == damage_gra_val]

                                if not save_gdf_to_shapefile(output_path=categories_shape_path, epsg=epsg,
                                                             gdf_data=filtered_data):
                                    continue

                                print(f'Kategorinin segmentation mask dosyasi olusturuluyor. {categories_mask_path} - '
                                      f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

                                vector_rasterization(shape_path=categories_shape_path, output_bounds=temp_mask_bounds,
                                                     output_path=categories_mask_path, res_x=res_x, res_y=res_y,
                                                     burn_value=categories_dict[file_val]['rgb'])
                                if seg_mask_as_png:
                                    print(
                                        f'Kategorinin segmentation png dosyasi olusturuluyor. '
                                        f'{categories_mask_png_path} - '
                                        f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
                                    [_original_raster, _alpha_channel, _geo_transform, _min_x, _max_y, _res_x, _res_y,
                                     _width, _height, _epsg, _geom_poly] = get_array_from_raster(
                                        file_path=categories_mask_path, only_info=False)

                                    save_raster_as_png(raster_array=_original_raster,
                                                       output_path=categories_mask_png_path,
                                                       generate_alpha=False)

                                    categories_seg_list.append(categories_mask_png_path)
                                    added_seg_list = True
                                else:
                                    categories_seg_list.append(categories_mask_path)
                                    added_seg_list = True

                    if seg_mask_as_png:
                        seg_mask_png_path = generate_temp_file_path(output_path=output_dir,
                                                                    file_name=temp_file_name + "_seg",
                                                                    file_ext='png')
                        print(f'Raster\'a ait tum segmantation png dosyasi olusturuluyor. {seg_mask_png_path} - '
                              f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

                        [_original_raster, _alpha_channel, _geo_transform, _min_x, _max_y, _res_x, _res_y, _width,
                         _height,
                         _epsg, _geom_poly] = get_array_from_raster(file_path=seg_mask_path, only_info=False)

                        save_raster_as_png(raster_array=_original_raster, output_path=seg_mask_png_path,
                                           generate_alpha=False)

                        if not added_seg_list:
                            seg_list.append(seg_mask_png_path)
                    else:
                        if not added_seg_list:
                            seg_list.append(seg_mask_path)

    ds = None

    if convert_coco:
        categories_path = generate_temp_file_path(output_path=output_dir, file_name='categories', file_ext='json')
        write_json(output_path=categories_path, json_data=categories_dict)

        categories_seg_list.extend(seg_list)
        label_list = list(set(categories_seg_list))

        annotations_dict = start_conversion_coco(image_list=image_list, width=width, height=height, seg_list=label_list,
                                                 raster_name=raster_name, description="pre_annotation_sample",
                                                 categories_dict=categories_dict)

        write_json(output_path=annotations_path, json_data=annotations_dict)

    delete_file(file_path=raster_path_4326)

    print(f'Islem tamamlandi - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
