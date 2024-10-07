from flask import Flask, request, jsonify, send_file, make_response, redirect
import requests
from PIL import Image, ImageColor
from io import BytesIO
from datetime import datetime, timedelta, UTC
import logging
import os
import sys

import ImageGenerator
import ImageLoader
from Layout import H_align, V_align
import Auth


RESPONSE_IMAGE_COUNT = 100
PORT = 8080
FONT_MAP = {
    #"Helvetica": "Helvetica-Bold.ttf",
    "Helvetica kursiv": "Helvetica-BoldOblique.ttf",
    "Helvetica": "helvetica-rounded-bold.otf",
    "Arathevil": "ArathevilBontegliar.otf",
    "Palace Script": "Palace script.ttf"
}


logging.basicConfig(filename="backend.log", level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

UPLOAD_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), '../images'))
FRONTEND_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), '../build'))

app = Flask(__name__, static_folder=FRONTEND_DIRECTORY, static_url_path='/')
app.config['UPLOAD_FOLDER'] = UPLOAD_DIRECTORY


with open("saved_urls.txt", "a") as storage_file:
    storage_file.write(str(datetime.now()) + "\n")


def create_unauthorized_response():
    return redirect("/login", 302)


@app.route("/api/login", strict_slashes=False, methods=['POST'])
def try_login():
    password = request.get_data(as_text=True)
    if Auth.check_password(password):
        token = Auth.create_new_token()
        response = redirect("/", 200)
        expiration_time = datetime.now() + timedelta(milliseconds=Auth.TOKEN_LIFETIME)
        http_expiration_time = expiration_time.strftime('%a, %d %b %Y %H:%M:%S GMT')
        response.headers.add("Set-Cookie", "auth=" + token + "; Expires=" + http_expiration_time) 
        logging.info("A user successfully logged in. Token: " + token)
        return response
    else:
        logging.info("A user tried to login with the wrong password.")
        response = make_response()
        response.status = 401
        response.data = "Wrong password."
        return response


@app.route("/api/images", strict_slashes=False)
def get_image_ids():
    is_authorized = Auth.token_is_authorized(request.cookies.get("auth"))
    if not is_authorized:
        return create_unauthorized_response()

    return ImageLoader.get_all_image_ids()[-RESPONSE_IMAGE_COUNT:]



@app.route("/api/images/<image_id>", strict_slashes=False, methods=['GET'])
def get_image(image_id): 
    is_authorized = Auth.token_is_authorized(request.cookies.get("auth"))
    if not is_authorized:
        return create_unauthorized_response()

    if not ImageLoader.image_exists(image_id):
        return "Das Bild existiert nicht", 404

    filepath = ImageLoader.get_image_path(image_id)
    return send_file(filepath, "image/jpg")


@app.route("/api/images/<image_id>", strict_slashes=False, methods=['POST'])
def post_image(image_id):
    is_authorized = Auth.token_is_admin_authorized(request.cookies.get("auth"))
    if not is_authorized:
        return create_unauthorized_response()
    #TODO: create image from body
    file = request.files.getlist('files')
    print(request.files, "....")
    for f in file:
        print(f.filename)
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], f.filename))
    return "Successfully saved image " + f.filename


def trim_request_data_to_url(data):
    payload = str(data)
    url = payload[2:(len(payload) - 1)]
    return url


@app.route("/api/images/<image_id>/save", strict_slashes=False, methods=['POST'])
def save_url(image_id):
    is_authorized = Auth.token_is_authorized(request.cookies.get("auth"))
    if not is_authorized:
        return create_unauthorized_response()

    url = trim_request_data_to_url(request.get_data())
    with open("saved_urls.txt", "a") as storage_file:
        storage_file.write(url + "\n")
    return "Successfully saved image url"

global saved_image_counter
saved_image_counter = 0
@app.route("/api/images/<image_id>/save_raw", strict_slashes=False, methods = ['POST'])
def save_image(image_id):
    is_authorized = Auth.token_is_authorized(request.cookies.get("auth"))
    if not is_authorized:
        return create_unauthorized_response()

    url = trim_request_data_to_url(request.get_data())
    global saved_image_counter
    image_data = requests.get("http://localhost:{}/images/{}".format(PORT, url)).content
    image = Image.open(BytesIO(image_data))
    image.save("storage/img_" + str(image_id) + "_" + str(saved_image_counter) + ".jpg")
    saved_image_counter += 1
    return "Successfully saved image"


@app.route("/api/images/<image_id>/thumbnail", strict_slashes=False)
def get_thumbnail(image_id):
    is_authorized = Auth.token_is_authorized(request.cookies.get("auth"))
    if not is_authorized:
        return create_unauthorized_response()

    if not ImageLoader.image_exists(image_id):
        return "Das Bild existiert nicht", 404

    filepath = ImageLoader.get_cache_path(image_id, "thumbnail")
    
    if not ImageLoader.image_exists_at_path(filepath):
        ImageGenerator.generate_thumbnail(image_id, filepath)

    return send_file(filepath, "image/jpg")


@app.route("/api/images/<image_id>/grayscale", strict_slashes=False)
def get_grayscale(image_id):
    is_authorized = Auth.token_is_authorized(request.cookies.get("auth"))
    if not is_authorized:
        return create_unauthorized_response()

    if not ImageLoader.image_exists(image_id):
        return "Das Bild existiert nicht", 404

    filepath = ImageLoader.get_cache_path(image_id, "grayscale")

    if not ImageLoader.image_exists_at_path(filepath):
        ImageGenerator.generate_grayscale(image_id, filepath)

    return send_file(filepath, "image/jpg")


#@app.route("/api/images/<image_id>/occasion", strict_slashes=False)
def get_occasion(image_id):
    is_authorized = Auth.token_is_authorized(request.cookies.get("auth"))
    if not is_authorized:
        return create_unauthorized_response()

    if not ImageLoader.image_exists(image_id):
        return "Das Bild existiert nicht", 404

    filepath = ImageLoader.get_cache_path(image_id, "occasion")

    if not ImageLoader.image_exists_at_path(filepath):
        ImageGenerator.generate_overlay(image_id, "Silvester2024", filepath)

    return send_file(filepath, "image/jpg")



# Sample URL request:
#   http://127.0.0.1:5000/images/000226/personalized?text=Jugend%20Silvesterfeier%0A2023&font=Arathevil&font_size=300&H_align=center&v_align=top&color=%232525A5
@app.route("/api/images/<image_id>/personalized", strict_slashes=False)
def get_personalized(image_id):
    is_authorized = Auth.token_is_authorized(request.cookies.get("auth"))
    if not is_authorized:
        return create_unauthorized_response()

    if not ImageLoader.image_exists(image_id):
        return "Das Bild existiert nicht", 404

    filepath = ImageLoader.get_cache_path(image_id, "personalized")

    text = request.args.get("text")
    font = FONT_MAP[request.args.get("font")]
    font_size = int(float(request.args.get("font_size")))
    h_align = H_align(request.args.get("h_align"))
    v_align = V_align(request.args.get("v_align"))
    color = ImageColor.getrgb(request.args.get("color"))

    if(len(text) == 0):
        return get_image(image_id)

    ImageGenerator.generate_personalized(image_id, text, font, font_size, h_align, v_align, color, filepath)

    return send_file(filepath, "image/jpg")


@app.route("/", strict_slashes=False, methods=['GET'])
def index():
    return app.send_static_file('index.html')


@app.errorhandler(404)
def frontend_proxy(path):
    logging.debug("Proxying to frontend...")
    return app.send_static_file('index.html')



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=PORT)
