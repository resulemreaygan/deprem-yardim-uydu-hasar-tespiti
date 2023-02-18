"""
Author: Resul Emre AYGAN
"""
import os.path
from json import dump, load
from uuid import uuid4


def write_json(output_path, json_data):
    with open(output_path, "w") as f:
        dump(json_data, f, indent=4)


def load_json(json_path):
    with open(json_path) as json_data_file:
        data = load(json_data_file)

    return data


def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)


def file_exists(file_path):
    return os.path.exists(file_path)


def get_file_name(file_path):
    return os.path.split(file_path)[1].split('.')[0]


def generate_temp_raster_path(output_path, raster_name=''):
    if raster_name == '':
        raster_name = str(uuid4())

    return os.path.join(output_path, raster_name + '.tif')


def generate_temp_file_path(output_path, file_ext, file_name=''):
    if file_name == '':
        file_name = str(uuid4())

    return os.path.join(output_path, file_name + '.' + file_ext)
