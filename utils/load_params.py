"""
Author: Resul Emre AYGAN
"""

from sys import exit
from utils.file_operations import file_exists, load_json


def load_config():
    try:
        if not file_exists(file_path="config.json"):
            print(f"Konfig dosyasi bulunamadi!")
            exit()

        data = load_json(json_path="config.json")

        save_as_png = data["save_as_png"]
        output_dir = data["output_dir"]
        crop_size_x = data["crop_size_x"]
        crop_size_y = data["crop_size_y"]
        crop_shape = data["crop_shape"]
        shape_path = data["shape_path"]
        raster_format = data["raster_format"]
        raster_path = data["raster_path"]
        seg_mask = data["seg_mask"]
        seg_mask_as_png = data["seg_mask_as_png"]
        convert_coco = data["convert_coco"]

        return [save_as_png, output_dir, crop_size_x, crop_size_y, crop_shape, shape_path, raster_format, raster_path,
                seg_mask, seg_mask_as_png, convert_coco]
    except Exception as error:
        print(f"Konfig dosyasi yuklenirken hata olustu! - Hata: {error}")
        exit()
