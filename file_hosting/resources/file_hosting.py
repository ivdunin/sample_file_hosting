# -*- coding: utf-8 -*-
# Copyright (c) 2018 Dunin Ilya.
"""  File Hosting service """

from datetime import datetime
from flask import abort, request, current_app, jsonify, make_response, Response
from flask_restful import Resource
from functools import wraps
from json import dump as dump_meta, load as load_meta
from os import path
from uuid import uuid4


def get_upload_path():
    """
    Get full path to upload folder
    :return:
    """
    return path.join(current_app.config.get('UPLOAD_FOLDER'))


def check_access_token(f):
    """
    Authorisation decorator
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.headers.get('X-API-KEY') != current_app.config.get('SECRET_KEY'):
            abort(401, 'Not authorised!')
        else:
            return f(*args, **kwargs)
    return wrapper


def check_file_size(f):
    """
    File size check decorator
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        file_size = int(request.headers.get('Content-Length'))
        limit = current_app.config.get('MAX_CONTENT_LENGTH')
        if file_size > limit:
            abort(400, 'Cannot upload file! File size {} exceeded limit {}'.format(file_size, limit))
        else:
            return f(*args, **kwargs)
    return wrapper


class FileHosting(Resource):
    def __init__(self):
        self.logger = current_app.logger

    @staticmethod
    def _get_meta_info():
        """
        Get File meta info (type and time to live on server)
        :return:
        """
        try:
            ttl = int(request.headers.get('TTL', current_app.config.get('TTL_DEFAULT')))
            if ttl <= 0:
                return None, 'TTL should be greater than 0!'

            ttl = min(ttl, current_app.config.get('TTL_MAX'))

            return ({'TTL': ttl,
                     'Content-Type': request.headers.get('Content-Type'),
                     'Created': datetime.now().isoformat()},
                    None)
        except ValueError:
            return None, 'TTL not an integer!'

    @check_access_token
    def get(self, fid):
        """
        Get file by fid with it content type
        Example:
        curl -v http://localhost:5000/files/5a02c2022d8111e88a4b0028f8351bd7 --output out.file \
        -H "X-API-KEY: 7ef0f4182d7b11e88a4b0028f8351bd7"
        :param fid: file fid
        :return: file as binary
        """
        current_app.logger.info('Host: {} requested file: {}'.format(request.headers.get('Host'), fid))

        file_name = path.join(get_upload_path(), fid)
        meta_file = path.join(get_upload_path(), '{}.meta'.format(fid))
        try:
            with open(meta_file) as meta:
                jsn = load_meta(meta)

            with open(file_name, 'rb') as fp:
                r = Response(fp.read(), mimetype=jsn['Content-Type'])
                r.status_code = 200
                return r
        except FileNotFoundError:
            abort(404, 'File not found on server!')
        except IOError as e:
            abort(400, 'Cannot read file: {}'.format(e))

    @check_access_token
    @check_file_size
    def post(self):
        """
        Store file on server
        Example:
        curl -v -H "X-API-KEY: 7ef0f4182d7b11e88a4b0028f8351bd7" -X POST --data-binary @test.png \
        -H "Content-Type: image/png" http://localhost:5000/files
        :return: 201 if file created, else error code
        """
        if not request.headers.get('Content-Type'):
            abort(400, 'Empty Content-Type header!')

        if len(request.data) == 0:  # this will occur if user will send incorrect Content-Type
            abort(400, 'Incorrect request! Empty request data, nothing to store!')

        meta_info = self._get_meta_info()
        if not meta_info[0]:
            abort(400, meta_info[1])

        try:
            fid = uuid4().hex
            file_name = path.join(get_upload_path(), fid)
            meta_file = path.join(get_upload_path(), '{}.meta'.format(fid))

            try:
                with open(file_name, 'wb') as fp:
                    fp.write(request.data)

                with open(meta_file, 'w') as meta:
                    dump_meta(meta_info[0], meta, sort_keys=True)

                current_app.logger.info('Host: {} uploaded file: {}'.format(request.headers.get('Host'), fid))

            except IOError as e:
                abort(400, 'Cannot save file: {}'.format(e))

            return make_response(jsonify({'file': fid}), 201)
        except IOError as e:
            abort(400, e)

    @check_access_token
    @check_file_size
    def put(self, fid):
        """
        Update file on server by fid
        Example:
        curl -H "X-API-KEY: 7ef0f4182d7b11e88a4b0028f8351bd7" -H "Content-Type: image/png" \
        --upload-file test2.png  http://localhost:5000/files/52347ac4306b11e88a4b0028f8351bd7 -v
        :param fid: file fid
        :return: status 200 if successful, else error code
        """
        if not request.headers.get('Content-Type'):
            abort(400, 'Empty Content-Type header!')

        file_name = path.join(get_upload_path(), fid)
        meta_file = path.join(get_upload_path(), '{}.meta'.format(fid))
        try:
            if not path.exists(file_name):
                abort(404, 'File not found on server!')

            with open(meta_file) as meta:
                jsn = load_meta(meta)

            with open(file_name, 'wb') as fp:
                fp.write(request.data)

            jsn['Content-Type'] = request.headers.get('Content-Type')

            with open(meta_file, 'w') as meta:
                dump_meta(jsn, meta, sort_keys=True)
            current_app.logger.info('Host: {} updated file: {}'.format(request.headers.get('Host'), fid))
            return make_response(jsonify({'file': fid}), 200)
        except IOError as e:
            abort(400, e)

