import ImageLoader
import ImageEditor
from PIL import ImageFont

#This class generates Image Editions and stores them in the cache


def generate_thumbnail(image_id, filepath):
    original = ImageLoader.load_image(image_id)
    thumbnail = ImageEditor.create_thumbnail(original)
    thumbnail.save(filepath)


def generate_personalized(image_id, text, font, font_size, h_align, v_align, color, filepath):
    original = ImageLoader.load_image(image_id)
    font = ImageFont.truetype("fonts/" + font, font_size)
    personalized = ImageEditor.create_personalized(original, text, font, h_align, v_align, color)
    personalized.save(filepath)


def generate_grayscale(image_id, filepath):
    original = ImageLoader.load_image(image_id)
    grayscale = ImageEditor.create_grayscale(original)
    grayscale.save(filepath)


def generate_overlay(image_id, overlay_name, filepath):
    original = ImageLoader.load_image(image_id)
    overlay = ImageLoader.load_overlay(overlay_name)
    image = ImageEditor.create_overlay(original, overlay)
    image.save(filepath)

