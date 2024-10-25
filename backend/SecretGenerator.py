from hashlib import sha256

def generate_secret(password):
    encoded_password = password.encode('utf-8')
    hash = sha256(encoded_password).hexdigest()
    with open("config/secret.conf", "w") as conf:
        conf.write(hash)