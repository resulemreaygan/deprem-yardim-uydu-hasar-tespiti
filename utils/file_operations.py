"""
Author: Resul Emre AYGAN
"""

from json import dump, load
from os import makedirs, path, remove
from uuid import uuid4


def write_json(output_path, json_data):
    with open(output_path, "w") as f:
        dump(json_data, f, indent=4)


def load_json(json_path):
    with open(json_path) as json_data_file:
        data = load(json_data_file)

    return data


def delete_file(file_path):
    if path.exists(file_path):
        remove(file_path)


def file_exists(file_path):
    return path.exists(file_path)


def is_dir(dir_path):
    return path.isdir(dir_path)


def is_file(file_path):
    return path.isfile(file_path)


def generate_dir(dir_path):
    makedirs(dir_path, exist_ok=True)


def get_file_name(file_path):
    return get_file_name_with_ext(file_path=file_path).split('.')[0]


def get_file_name_with_ext(file_path):
    return path.split(file_path)[1]


def generate_temp_file_path(output_path, file_ext, file_name=''):
    if file_name == '':
        file_name = str(uuid4())

    return path.join(output_path, file_name + '.' + file_ext)
