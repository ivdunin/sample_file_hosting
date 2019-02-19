# -*- coding: utf-8 -*-
# Copyright (c) 2018 Dunin Ilya.
""" Main Service file """

from os import path, makedirs
from flask import Flask
from flask_restful import Api
from file_hosting.resources.file_hosting import FileHosting

app = Flask(__name__)
app.config.from_object('file_hosting.settings.development')

api = Api(app)
api.add_resource(FileHosting, '/files', '/files/<fid>')


if __name__ == '__main__':
    print(app.config)
    context = None  # pylint: disable=invalid-name
    if not app.config.get('DEBUG'):
        context = (app.config.get('ROOT_CERT'), app.config.get('PRIVATE_KEY'))  # pylint: disable=invalid-name

    if not path.exists(path.join(app.root_path, app.config.get('UPLOAD_FOLDER'))):
        makedirs(path.join(app.root_path, app.config.get('UPLOAD_FOLDER')))

    try:
        app.run(
            host=app.config.get('HOST'),
            port=app.config.get('PORT'),
            debug=app.config.get('DEBUG'),
            ssl_context=context
        )
    except FileNotFoundError as exc:
        app.logger.error('Cannot load certificate: {}'
                         '\nCheck settings/production.json "ROOT_CERT" and "PRIVATE_KEY" values'.format(exc))
        exit(1)
