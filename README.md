# file_hosting

1
234

Sample service which allow to temporary store JSON files between services.

## Quick Start

Run the application:

    # Create virtual env and install all dependenies
    cd file_hosting
    FLASK_APP=app.py FLASK_ENV=development flask run
    or
    FLASK_APP=app.py flask run

And check it in the browser at [http://127.0.0.1:5500/](http://127.0.0.1:5000/)

## Usage

* Upload file to service:

    `curl -H "X-API-KEY: [key]" -H "TTL: 2" -X POST --data-binary @[file] -H "Content-Type: [mime-type]" http://localhost:5000/files`

* Download uploaded file:

    `curl -H "X-API-KEY: [key]" http://localhost:5000/files/[id] --output out.file"`

* Replace uploaded file with new one:

    `curl -H "X-API-KEY: [key]" -H "Content-Type: [mime-type]" --upload-file [file] http://localhost:5000/files/[id]`


where:
1. **X-API-KEY** -- secret key for authentication, mandatory.
2. **Content-Type** -- file mime-type (possible values: `application/json`, `application/octet-stream`, `image/png`), mandatory
3. **TTL** -- time-to-live (retention time) in hours. Time how long to store files on server

## Service configuration
Service settings stores in: `file_hosting/file_hosting/settings/development.py`

* *DEBUG* -- DEBUG mode (True | False)
* *UPLOAD_FOLDER* -- path to store uploaded files
* *SECRET_KEY* -- access key for clients. You can generate it with: `python3 -c "import uuid; print(uuid.uuid4().hex)"`
* *MAX_CONTENT_LENGTH* -- uploaded file size limit
* *TTL_MAX* -- maximum retention (time-to-live) time in hours
* *TTL_DEFAULT* -- default retention (time-to-live) time in hours (if not specified in `POST` command)
* *HOST* -- host for connections `0.0.0.0` or `127.0.0.1`
* *PORT* -- port for connections
* *ROOT_CERT* -- path to root certificate for SSL connections
* *PRIVATE_KEY* -- path to private key for SSL connections
