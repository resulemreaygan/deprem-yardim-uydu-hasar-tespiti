"""
Author: Resul Emre AYGAN
"""

from datetime import datetime

from coco_operations import draw_coco_labels, calc_annotations_statistics
from utils.file_operations import load_json
from utils.load_params import load_config

if __name__ == '__main__':
    print(f'Cizim islemi basladi - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

    [save_as_png, output_dir, crop_size_x, crop_size_y, crop_shape, shape_path, raster_format, raster_path,
     seg_mask, seg_mask_as_png, convert_coco, visualize_coco, annotations_path,
     annotations_image_path, drawn_annotations_path, calculate_annotations_analysis] = load_config()

    if not visualize_coco:
        raise Exception(f"Visualize coco parametresi true olmali! visualize_coco={visualize_coco}")

    ann_dict = load_json(json_path=annotations_path)

    draw_coco_labels(annotations_dict=ann_dict, annotations_image_path=annotations_image_path,
                     drawn_annotations_path=drawn_annotations_path)

    print(f'Cizim islemi tamamlandi - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

    if calculate_annotations_analysis:
        print(f'Etiket analizi basladi - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

        calc_annotations_statistics(annotations_dict=ann_dict, statistics_path=drawn_annotations_path)

        print(f'Etiket analizi tamamlandi - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
