"""
Author: Resul Emre AYGAN
"""

import re
import os.path
from datetime import datetime
from PIL import Image, ImageDraw
from geometry_operations import Polygon
import numpy as np
from skimage import measure
import json

model_class = {"No visible damage": "undamaged", "Destroyed": "damaged",
               "Possibly damaged": "uncertain", "Damaged": "uncertain", "": "buildings"}

color_mapping = {
    'undamaged': {'id': 1, 'rgb': [0, 255, 0]},
    'damaged': {'id': 2, 'rgb': [255, 0, 0]},
    'uncertain': {'id': 3, 'rgb': [255, 255, 0]},
    'buildings': {'id': 4, 'rgb': [255, 255, 255]}
}


def write_licenses(name, index=1, url=""):
    licenses_dict = {
        "licenses": {
            "name": name,
            "id": index,
            "url": url,
        }
    }

    return licenses_dict


def write_info(description="AYA", contributor="AYA - Uydu"):
    datetime_info = datetime.now()
    info_dict = {
        "info": {
            "contributor": contributor,
            "date_created": datetime_info.strftime("%Y-%m-%d"),
            "description": description,
            "url": "",
            "version": "",
            "year": datetime_info.strftime("%Y")
        }
    }

    return info_dict


def write_categories(categories_list):
    categories_dict = {"categories": []}

    for index, category in enumerate(categories_list):
        category_dict = {"id": index + 1, "name": category, "supercategory": "Buildings"}
        categories_dict["categories"].append(category_dict)

    return categories_dict


def write_images(image_list, width=0, height=0):
    images_dict = {"images": []}
    images_ids = {}

    for index, file in enumerate(image_list):
        if width != 0 or height != 0:
            img = Image.open(file)
            width, height = img.size

        file_name = os.path.split(file)[1]

        image = {"id": index + 1, "width": width, "height": height, "file_name": file_name}

        images_dict["images"].append(image)

        images_ids[file_name] = index + 1

    return images_dict, images_ids


def create_sub_masks(mask_image, colors):
    width, height = mask_image.size

    sub_masks = {}

    for x in range(width):
        for y in range(height):
            pixel = mask_image.getpixel((x, y))

            if pixel in colors:
                sub_mask = sub_masks.get(pixel)
                if sub_mask is None:
                    sub_masks[pixel] = Image.new("1", (width + 2, height + 2))

                sub_masks[pixel].putpixel((x + 1, y + 1), 1)

    return sub_masks


def write_annotations(label_list, images_ids, is_crowd, categories):
    annotations_dict = {"annotations": []}

    annotation_id = 1

    colors = [tuple(group["rgb"]) for group in categories.values()]

    for file in label_list:
        print(file)

        mask = Image.open(file)
        mask = mask.convert("RGB")

        sub = create_sub_masks(mask_image=mask, colors=colors)

        file_name = re.sub('_seg', '', os.path.split(file)[1])

        # image_id = images_ids[file_name]

        annotations = []

        for rgb, sub_mask in sub.items():
            for key, value in categories.items():
                if tuple(value["rgb"]) == rgb:
                    file_name = re.sub('_' + key, '', file_name)
                    category_id = value["id"]
                    image_id = images_ids[file_name]
                    break

            # for rgb, sub_mask in sub.items():
            #     for record in categories.keys():
            #         if '_' + record in file_name:
            #             file_name = re.sub('_' + record, '', file_name)
            #             category_id = categories[record]['id']
            #             image_id = images_ids[file_name]
            #             break

            last_annotation_id, annotations_new = create_sub_mask_annotation(sub_mask=sub_mask, image_id=image_id,
                                                                             category_id=category_id,
                                                                             annotation_id=annotation_id,
                                                                             is_crowd=is_crowd)
            annotation_id = last_annotation_id + 1
            annotations += annotations_new

        annotations_dict["annotations"] += annotations

    return annotations_dict


def create_sub_mask_annotation(sub_mask, image_id, category_id, annotation_id, is_crowd):
    contours = measure.find_contours(sub_mask, 0.5, positive_orientation="low")

    annotations = []
    for contour in contours:
        for i in range(len(contour)):
            row, col = contour[i]
            contour[i] = (col - 1, row - 1)

        poly = Polygon(contour)
        poly = poly.simplify(1.0, preserve_topology=False)
        if not poly.is_empty:
            segmentation = np.array(poly.exterior.coords).ravel().tolist()

            x, y, max_x, max_y = poly.bounds
            width = max_x - x
            height = max_y - y
            bbox = (x, y, width, height)
            area = poly.area

            annotation = {
                "segmentation": [segmentation],
                "iscrowd": int(is_crowd),
                "image_id": int(image_id),
                "category_id": int(category_id),
                "id": int(annotation_id),
                "bbox": bbox,
                "area": area,
            }

            annotation_id += 1
            annotations.append(annotation)

    last_annotation_id = annotation_id
    return last_annotation_id, annotations


def write_json(output_path, json_data):
    with open(output_path, "w") as f:
        json.dump(json_data, f, indent=4)


def start_conversion_coco(raster_name, image_list, width, height, seg_list, description, categories_dict):
    licenses_dict = write_licenses(name=raster_name)
    info_dict = write_info(description=description)
    images_dict, images_ids = write_images(image_list=image_list, width=width, height=height)
    annotations_dict = write_annotations(label_list=seg_list, images_ids=images_ids, is_crowd=False,
                                         categories=categories_dict)
    categories_dict = write_categories(categories_list=list(categories_dict.keys()))

    annotations_dict = {
        **licenses_dict,
        **info_dict,
        **images_dict,
        **annotations_dict,
        **categories_dict,
    }

    return annotations_dict


def check_categories(categories):
    if categories:
        categories_dict = {model_class[val]: color_mapping[model_class[val]]
                           for val in categories if val in model_class}
        if categories_dict:
            return categories_dict
        else:
            return {'buildings': {'id': 4, 'rgb': [255, 255, 255]}}
    else:
        return {'buildings': {'id': 4, 'rgb': [255, 255, 255]}}


def draw_coco_labels(annotations_dict, annotations_image_path, drawn_annotations_path):
    annotations_by_image = {}

    for annotation in annotations_dict["annotations"]:
        image_id = annotation["image_id"]
        if image_id not in annotations_by_image:
            annotations_by_image[image_id] = []
        annotations_by_image[image_id].append(annotation)

    for image in annotations_dict["images"]:
        image_path = os.path.join(annotations_image_path, image["file_name"])
        image_data = Image.open(image_path)

        annotations = annotations_by_image.get(image["id"], [])

        draw_image = Image.new("RGB", image_data.size)
        draw = ImageDraw.Draw(draw_image)

        for annotation in annotations:
            bbox = annotation["bbox"]
            x, y, w, h = bbox
            x1, y1, x2, y2 = x, y, x + w, y + h

            category_name = annotations_dict["categories"][annotation["category_id"] - 1]["name"]

            if category_name in color_mapping.keys():
                rgb_value = tuple(color_mapping[category_name]['rgb'])
            else:
                rgb_value = (255, 0, 0)

            draw.rectangle([x1, y1, x2, y2], outline=rgb_value)

            draw.text((x1, y1), category_name, fill=rgb_value)

        draw_image = draw_image.convert(image_data.mode)

        draw_image = draw_image.resize(image_data.size)

        merged_image = Image.blend(image_data, draw_image, alpha=0.5)

        labeled_image_path = os.path.join(drawn_annotations_path, image["file_name"].split('.')[0] + '.png')
        merged_image.save(labeled_image_path)
