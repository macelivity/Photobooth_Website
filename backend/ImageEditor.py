from PIL import Image, ImageOps, ImageEnhance, ImageDraw
from ImageLoader import get_cache_path
from Layout import H_align, V_align


THUMBNAIL_MAX_SIZE = (320, 320)
TEXT_MARGIN = (120, 50)


def create_thumbnail(image):
    image.thumbnail(THUMBNAIL_MAX_SIZE)
    return image


def get_text_pixel_width(text, font):
    return font.getmask(text).getbbox()[2]

def get_text_pixel_height(text, font):
    ascent, descent = font.getmetrics()
    return font.getmask(text).getbbox()[3] + descent

def draw_text_on_image(drawer, image, text, font, color, h_align, v_align):
    xPos = 0
    yPos = 0

    if h_align == H_align.LEFT:
        xPos = TEXT_MARGIN[0]
    elif h_align == H_align.CENTER:
        xPos = (image.width - get_text_pixel_width(text, font)) / 2
    elif h_align == H_align.RIGHT:
        xPos = image.width - get_text_pixel_width(text, font) - TEXT_MARGIN[0]

    if v_align == V_align.TOP:
        yPos = TEXT_MARGIN[1]
    elif v_align == V_align.BOTTOM:
        yPos = image.height - get_text_pixel_height(text, font) - TEXT_MARGIN[1]

    drawer.text((xPos, yPos), text, font=font, align=h_align, fill=color)


def create_personalized(image, text, font, h_align, v_align, color):
    drawer = ImageDraw.Draw(image)

    if h_align == H_align.SPLIT:
        sections = text.split("<split/>")
        draw_text_on_image(drawer, image, sections[0], font, color, align='left')
        draw_text_on_image(drawer, image, sections[1], font, color, align='center')
        draw_text_on_image(drawer, image, sections[2], font, color, align='right')

    else:
        draw_text_on_image(drawer, image, text, font, color, h_align, v_align)

    return drawer._image


def create_grayscale(image):
    grayscale_image_raw = ImageOps.grayscale(image)

    contrast_enhancer = ImageEnhance.Contrast(grayscale_image_raw)
    grayscale_image = contrast_enhancer.enhance(1.1)

    return grayscale_image


def create_overlay(image, overlay):
    image.paste(overlay, (0,0), overlay)
    return image