from flask import Flask, request, jsonify, send_file, make_response, redirect
import requests
import json
from PIL import Image, ImageColor
from io import BytesIO
from datetime import datetime, timedelta, timezone
import logging
import os
import sys

import ImageGenerator
import ImageLoader
from Layout import H_align, V_align
import Auth


RESPONSE_IMAGE_COUNT = 100
PORT = 8447
FONT_MAP = {
    #"Helvetica": "Helvetica-Bold.ttf",
    "Helvetica kursiv": "Helvetica-BoldOblique.ttf",
    "Helvetica": "helvetica-rounded-bold.otf",
    "Arathevil": "ArathevilBontegliar.otf",
    "Palace Script": "Palace script.ttf"
}
FOTOBOX_URL = "http://85.16.197.116:5050"
#FOTOBOX_URL = "http://192.168.178.98:5050"

UPLOAD_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), '../images'))
FRONTEND_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), '../build'))


logging.basicConfig(filename="backend.log", level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


global printer_responses
printer_responses = {}


app = Flask(__name__, static_folder=FRONTEND_DIRECTORY, static_url_path='/')
app.config['UPLOAD_FOLDER'] = UPLOAD_DIRECTORY


with open("saved_urls.txt", "a") as storage_file:
    storage_file.write(str(datetime.now()) + "\n")


def create_unauthorized_response():
    return redirect("/login", 302)


@app.route("/api/login/printer", strict_slashes=False, methods=['POST'])
def try_login_printer():
    password = request.get_data(as_text=True)
    if Auth.check_password(password):
        token = Auth.create_new_token()
        response = make_response()
        response.staus = 200
        response.data = token
        logging.info("A printer successfully logged in. Token: " + token)
        return response
    else:
        logging.info("A user tried to login with the wrong password.")
        response = make_response()
        response.status = 401
        response.data = "Wrong password."
        return response


@app.route("/api/login", strict_slashes=False, methods=['POST'])
def try_login():
    password = request.get_data(as_text=True)
    if Auth.check_password(password):
        token = Auth.create_new_token()
        response = redirect("/", 200)
        expiration_time = datetime.now(timezone.utc) + timedelta(seconds=Auth.TOKEN_LIFETIME)
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


@app.route("/api/images/<image_id>/print", strict_slashes=False, methods=['POST'])
def print_image(image_id):
    try:
        response = requests.post(FOTOBOX_URL + "/printer/order", json={ 'image_id': image_id })
        return make_response(response.text, response.status_code)
    except Exception as e:
        print(e)
        return make_response("FAILURE", 500)


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
    print("[URL] http://localhost:{}/api/images/{}".format(PORT, url))
    image_data = requests.get("http://localhost:{}/api/images/{}".format(PORT, url)).content
    print(image_data)
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



def tick_printer_response(subpath, method, response_code):
    global printer_responses
    key = method + "_" + subpath
    if not key in printer_responses:
        printer_responses[key] = {}

    if not response_code in printer_responses[key]:
        printer_responses[key][response_code] = 1
    else:
        printer_responses[key][response_code] = printer_responses[key][response_code] + 1


@app.route("/api/printer/<path:subpath>", strict_slashes=False, methods=['GET', 'POST'])
def printer_proxy(subpath):
    logging.debug("Proxying to printer... [" + request.method + " " + subpath + "]")

    if request.method == 'GET':
        try:
            # Accepts only json
            response = requests.get(FOTOBOX_URL + "/printer/" + subpath)
            tick_printer_response(subpath, "GET", response.status_code)
            return make_response(response.json(), response.status_code)
        except Exception as e:
            print(e)
            tick_printer_response(subpath, "GET", 500)
            return make_response("FAILURE", 500)

    if request.method == 'POST':
        try:
            response = requests.post(FOTOBOX_URL + "/printer/" + subpath, json=request.json)
            tick_printer_response(subpath, "POST", response.status_code)
            return make_response(response.text, response.status_code)
        except Exception as e:
            print(e)
            tick_printer_response(subpath, "POST", 500)
            return make_response("FAILURE", 500)


@app.route("/api/admin/printer_responses", strict_slashes=False, methods=['GET'])
def get_printer_responses():
    global printer_responses
    return make_response(jsonify(printer_responses), 200)


@app.route("/", strict_slashes=False, methods=['GET'])
def index():
    return app.send_static_file('index.html')


@app.errorhandler(404)
def frontend_proxy(path):
    logging.debug("Proxying to frontend...")
    return app.send_static_file('index.html')



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=PORT)
