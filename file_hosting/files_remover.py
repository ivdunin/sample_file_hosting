#!/usr/bin/env python
# Copyright (c) 2018 Dunin Ilya.
""" Remove old files (job for cron) """

from datetime import datetime
from glob import glob
from json import load
from os import chdir, path, remove
from sys import stderr
from settings.development import UPLOAD_FOLDER


ISO_DATE_FMT = '%Y-%m-%dT%H:%M:%S.%f'


def remove_file(file_name):
    """
    Remove file method
    :param file_name: file name
    """
    try:
        remove(file_name)
        print('File "{}" successfully deleted!'.format(file_name))
    except IOError as e:
        print('Cannot remove file: {}\n{}'.format(file_name, e), file=stderr)


if __name__ == '__main__':
    cur_dir = path.join(path.dirname(__file__), UPLOAD_FOLDER)

    chdir(cur_dir)
    for meta in glob('*.meta'):
        with open(meta) as fp:
            print(f'Processing file: "{meta}"... ', end='')
            jsn = load(fp)
            created = datetime.strptime(jsn['Created'], ISO_DATE_FMT)
            ttl = jsn['TTL']
            delta = (datetime.now() - created).total_seconds()

            if delta < (ttl * 3600):
                print('deleting!')
                remove_file(path.splitext(meta)[0])
                remove_file(meta)
            else:
                print('keeping!')



