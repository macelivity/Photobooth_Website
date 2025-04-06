import secrets
from hashlib import sha256
import threading
import time


TOKEN_LENGTH = 64
TOKEN_LIFETIME = 14400  # 4h

SECRET_FILEPATH = "config/secret.conf"
AUTH_ACTIVE = False

global hashed_password

with open(SECRET_FILEPATH) as secret:
    hashed_password = secret.read() 


global tokens
tokens = set()


def check_password(password):
    if not AUTH_ACTIVE:
        return True
    encoded_password = password.encode('utf-8')
    hash = sha256(encoded_password).hexdigest()
    global hashed_password
    return hash == hashed_password

def create_new_token():
    global tokens
    while True:
        token = secrets.token_urlsafe(TOKEN_LENGTH)
        if not tokens.__contains__(token):
            tokens.add(token)
            threading.Thread(target=automatic_token_destruction, args=(token,))
            return token


def token_is_authorized(token):
    if not AUTH_ACTIVE:
        return True
    global tokens
    return tokens.__contains__(token) and not token == None


def remove_token(token):
    global tokens
    tokens.remove(token)


def automatic_token_destruction(token):
    time.sleep(TOKEN_LIFETIME)
    remove_token(token)
