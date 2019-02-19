from os import path

ROOT_DIR = path.join(path.dirname(__file__), '..', '..')
DEBUG = True  # make sure DEBUG is off unless enabled explicitly otherwise
UPLOAD_FOLDER = path.join(ROOT_DIR, 'upload_dir')  # Full path to upload folder
SECRET_KEY = '7ef0f4182d7b11e88a4b0028f8351bd7'
MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1Mb
TTL_MAX = 24  # max time to live (hours)
TTL_DEFAULT = 2  # default time to live for file (hours)

# Server settings
HOST = '127.0.0.1'
PORT = 5050

# certificate for SSL
ROOT_CERT = '../../root.crt'
PRIVATE_KEY = '../../root.key'
