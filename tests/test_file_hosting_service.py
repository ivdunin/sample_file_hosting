import unittest
from json import loads
from collections import namedtuple
from os import path, remove, listdir, stat
from file_hosting.app import app

SECRET_KEY = 'dummy-secret'
API_PATH = '/files'


class FileHostingTestCase(unittest.TestCase):
    File = namedtuple('File', ['name', 'size'])

    def _get_meta(self, fid):
        """
        Get file meta info by fid
        :param fid: file unique identification string
        :return: meta information if file found, else None
        """
        try:
            with open('upload_dir/{}.meta'.format(fid)) as fp:
                return fp.read()
        except IOError:
            return None

    def setUp(self):
        """
        Configure test upload dir and secret key
        """
        app.config['UPLOAD_FOLDER'] = 'upload_dir'
        app.config['SECRET_KEY'] = SECRET_KEY

        self.app = app.test_client()

    def test_authorize(self):
        """
        Authorisation test for all API (get, post, put)
        """
        rv = self.app.get(API_PATH + '/fake')
        self.assertEqual(401, rv.status_code, 'Actual: {}, expected: {}'.format(rv.status_code, 401))

        rv = self.app.post(API_PATH)
        self.assertEqual(401, rv.status_code, 'Actual: {}, expected: {}'.format(rv.status_code, 401))

        rv = self.app.put(API_PATH + '/fake')
        self.assertEqual(401, rv.status_code, 'Actual: {}, expected: {}'.format(rv.status_code, 401))

    def test_upload(self):
        """
        Test file upload with correct Content-Type
        """
        test_data = [('test.json', 'application/json'),
                     ('test.json', 'application/octet-stream'),
                     ('test.png', 'image/png')]
        for test_file, mimetype in test_data:
            headers = {'X-API-KEY': SECRET_KEY, 'Content-Type': mimetype, 'TTL': 1}
            with open(test_file, 'rb') as fp:
                rv = self.app.post(API_PATH, headers=headers, data=fp.read())
                self.assertEqual(201, rv.status_code, 'Actual: {}, expected: {}'.format(rv.status_code, 201))

    def test_upload_with_incorrect_type(self):
        """
        Test file upload with incorrect Content-Type
        """
        test_data = [('test.json', 'multipart/form-data'),
                     ('test.json', 'application/x-www-form-urlencoded')]
        for test_file, mimetype in test_data:
            headers = {'X-API-KEY': SECRET_KEY, 'Content-Type': mimetype, 'TTL': 1}
            with open(test_file, 'rb') as fp:
                rv = self.app.post(API_PATH, headers=headers, data=fp.read())
                self.assertEqual(400, rv.status_code, 'Actual: {}, expected: {}'.format(rv.status_code, 400))

    def test_get_and_put(self):
        """
        Test Get and Put API.
        Verify that original size and type equal to returned.
        """
        headers_post = {'X-API-KEY': SECRET_KEY, 'Content-Type': 'application/json', 'TTL': 1}
        headers_get = {'X-API-KEY': SECRET_KEY}
        headers_put = {'X-API-KEY': SECRET_KEY, 'Content-Type': 'image/png'}

        test_file = self.File('test.json', stat('test.json').st_size)

        # Upload json file
        with open(test_file.name, 'rb') as fp:
            rv = self.app.post(API_PATH, headers=headers_post, data=fp.read())

            jsn = loads(rv.data.decode('utf-8'))
            self.assertIn('file', jsn, 'File key not found!')
            fid = jsn['file']
            self.assertIsNotNone(fid, 'Empty file identifier!')

        self.assertIn('application/json', self._get_meta(fid), 'Content-Type stored incorrectly!')

        # Test Get Api
        rv = self.app.get('{}/{}'.format(API_PATH, fid), headers=headers_get)
        self.assertEqual(200, rv.status_code, 'Actual: {}, expected: {}'.format(rv.status_code, 200))
        self.assertEqual(rv.content_length, test_file.size,
                         'Actual size: {} not equal to expected: {}'.format(rv.content_length, test_file.size))

        # Test Put Api
        test_file = self.File('test.png', stat('test.png').st_size)
        with open(test_file.name, 'rb') as fp:
            rv = self.app.put('{}/{}'.format(API_PATH, fid), data=fp.read(), headers=headers_put)
            self.assertEqual(200, rv.status_code, 'Actual: {}, expected: {}'.format(rv.status_code, 201))
            self.assertIn('image/png', self._get_meta(fid), 'Content-Type stored incorrectly!')

        # Test Get after Put
        rv = self.app.get('{}/{}'.format(API_PATH, fid), headers=headers_get)
        self.assertEqual(200, rv.status_code, 'Actual: {}, expected: {}'.format(rv.status_code, 200))
        self.assertEqual(rv.content_length, test_file.size,
                         'Actual size: {} not equal to expected: {}'.format(rv.content_length, test_file.size))

    def test_ttl(self):
        """
        Test correct ttl time
        1. ttl <= TTL_MAX
        2. empty ttl => TTL_DEFAULT
        3. (incorrect ttl, ttl <= 0) => 400, incorrect request
        """
        TTL_VALUE = namedtuple('TTL', ['value', 'response', 'stored_value'])
        ttl_values = (TTL_VALUE(0, 400, None),
                      TTL_VALUE("ttl", 400, None),
                      TTL_VALUE(None, 201, app.config.get('TTL_DEFAULT')),
                      TTL_VALUE(1, 201, 1),
                      TTL_VALUE(12, 201, 12),
                      TTL_VALUE(25, 201, app.config.get('TTL_MAX'))
            )
        for ttl in ttl_values:
            headers_post = {'X-API-KEY': SECRET_KEY, 'Content-Type': 'application/json'}
            if ttl.value is not None:
                headers_post['TTL'] = ttl.value

            with open('test.json', 'rb') as fp:
                rv = self.app.post(API_PATH, headers=headers_post, data=fp.read())
                self.assertEqual(ttl.response, rv.status_code,
                                 'Actual result {}; expected: {}; Data: {}'.format(rv.status_code, ttl.response, ttl))
                if ttl.response == 201:
                    jsn = loads(rv.data.decode('utf-8'))
                    fid = jsn['file']
                    meta_info = loads(self._get_meta(fid))
                    self.assertEqual(ttl.stored_value, meta_info.get('TTL'), 'TTL stored not correctly!')

    def tearDown(self):
        """
        Remove all temporary files after tests
        """
        for f in listdir(app.config['UPLOAD_FOLDER']):
            full_path = path.join(app.config['UPLOAD_FOLDER'], f)
            remove(full_path)


if __name__ == '__main__':
    unittest.main()
