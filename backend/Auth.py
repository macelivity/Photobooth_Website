import secrets
from hashlib import sha256
import threading
import time


TOKEN_LENGTH = 64
TOKEN_LIFETIME = 14400  # 4h

HASHED_PASSWORD = "eb2963dd2eb1431b0ad907d188450cdd6c9c127449b2dfdb23f0baaaa2b5b46f"


global tokens
tokens = set()


def check_password(password):
    encoded_password = password.encode('utf-8')
    hash = sha256(encoded_password).hexdigest()
    return hash == HASHED_PASSWORD

def create_new_token():
    global tokens
    while True:
        token = secrets.token_urlsafe(TOKEN_LENGTH)
        if not tokens.__contains__(token):
            tokens.add(token)
            threading.Thread(target=automatic_token_destruction, args=(token,))
            return token


def token_is_authorized(token):
    global tokens
    return tokens.__contains__(token) and not token == None


def remove_token(token):
    global tokens
    tokens.remove(token)


def automatic_token_destruction(token):
    time.sleep(TOKEN_LIFETIME)
    remove_token(token)
