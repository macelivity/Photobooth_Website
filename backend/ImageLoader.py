import os
from PIL import Image


ROOT_DIRECTORY = "/home/fotobox"
#ROOT_DIRECTORY = "../"
FILENAME_DIGIT_COUNT = 6


def normalize_id(id):
    return "0" * (FILENAME_DIGIT_COUNT - len(id)) + id


def get_filename(image_id, tag = None):
    if not tag:
        return "img" + image_id + ".jpg"
    else:
        return "img" + image_id + "_" + tag + ".jpg"


def get_image_path(image_id):
    return ROOT_DIRECTORY + "/images/" + get_filename(image_id)

def get_cache_path(image_id, tag):
    return ROOT_DIRECTORY + "/website/backend/cache/" + get_filename(image_id, tag)


def get_all_image_ids():
    titles = os.listdir(ROOT_DIRECTORY + "/images")
    titles.sort(reverse=True)
    #trim title strings to the number - remove "img_" letters and everything after the digits
    ids = [title[3:-4] for title in titles]
    return ids


def image_exists_at_path(path):
    return os.path.isfile(path)


def load_image(image_id):
    filepath = get_image_path(image_id)
    image = Image.open(filepath)
    return image


#occasion has to fit the filename
def load_overlay(occasion):
    filepath = ROOT_DIRECTORY + "/website/backend/overlays/" + occasion + ".png"
    overlay = Image.open(filepath)
    return overlay


def load_cache_image(image_id, tag):
    filepath = get_cache_path(image_id, tag)
    image = Image.open(filepath)
    return image

def image_exists(image_id):
    filepath = get_image_path(image_id)
    return image_exists_at_path(filepath)
