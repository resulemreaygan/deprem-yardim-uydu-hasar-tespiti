"""
Author: Resul Emre AYGAN
"""

from utils.file_operations import file_exists, load_json, is_dir, is_file, generate_dir


def load_config():
    try:
        if not file_exists(file_path="config.json"):
            raise Exception(f"Konfig dosyasi bulunamadi!")

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
        visualize_coco = data["visualize_coco"]
        coco_ann_path = data["coco_annotations_path"]
        coco_ann_image_path = data["annotations_image_dir_path"]
        drawn_annotations_path = data["drawn_annotations_path"]

        if not is_dir(dir_path=output_dir):
            raise Exception(f"Cikti dosya yolu dizin degil!")

        if not file_exists(file_path=output_dir):
            generate_dir(dir_path=output_dir)

        if crop_shape:
            if not is_file(file_path=shape_path):
                raise Exception(f"Shapefile dosya yolunda hata var!")
        else:
            convert_coco = False

        if visualize_coco:
            if not file_exists(file_path=coco_ann_path):
                raise Exception(f"Coco etiket verisi bulunamadi! - {coco_ann_path}")

            if not is_file(file_path=coco_ann_path):
                raise Exception(f"Coco etiket verisi dosya degil! - {coco_ann_path}")

            if not is_dir(dir_path=coco_ann_image_path):
                raise Exception(f"Coco etikete ait goruntu verisi dosya yolu dizin olmalidir! - {coco_ann_image_path}")

            if not is_dir(dir_path=drawn_annotations_path):
                raise Exception(f"Coco cikti dosya yolu dizin olmalidir! - {drawn_annotations_path}")

        return [save_as_png, output_dir, crop_size_x, crop_size_y, crop_shape, shape_path, raster_format, raster_path,
                seg_mask, seg_mask_as_png, convert_coco, visualize_coco, coco_ann_path, coco_ann_image_path,
                drawn_annotations_path]
    except Exception as error:
        raise Exception(f"Konfig dosyasi yuklenirken hata olustu! - Hata: {error}")
