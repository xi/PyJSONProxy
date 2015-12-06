from __future__ import absolute_import

import os
import sys

try:
	from urllib.request import urlopen as _urlopen
	from urllib.error import HTTPError
except ImportError:
	from urllib2 import urlopen as _urlopen
	from urllib2 import HTTPError

from flask import abort
from flask import current_app
from flask import Flask
from flask import jsonify
from flask import make_response
from flask import render_template
from flask import request
import cachetools

from .lib import check_config
from .lib import _doc
from .lib import ENDPOINTS
from .lib import parse_args
from .lib import scrape

app = Flask(__name__)


def get_config(endpoint):
	try:
		return current_app.config[ENDPOINTS][endpoint]
	except KeyError:
		abort(404)


@cachetools.ttl_cache()
def urlopen(url):
	try:
		current_app.logger.info('fetching %s' % url)
		original = _urlopen(url)

		body = original.read()
		code = original.getcode()
		headers = original.headers.items()

		return body, code, headers
	except HTTPError as error:
		abort(error.code)


@app.route('/<endpoint>/<path:path>', methods=['GET'])
def handle(endpoint, path):
	config = get_config(endpoint)
	url = request.url.replace(request.host_url + endpoint + '/', config['host'])

	body, code, headers = urlopen(url)

	if 'fields' in config:
		response = jsonify(scrape(url, body, config))
	else:
		response = make_response(body, code)

	if current_app.config.get('ALLOW_CORS', False):
		response.headers['Access-Control-Allow-Origin'] = '*'

	return response


@app.route('/', methods=['GET'])
def index():
	config = current_app.config[ENDPOINTS]
	data = [_doc(config[endpoint], endpoint) for endpoint in config]
	return render_template('index.html', endpoints=data)


@app.route('/<endpoint>/', methods=['GET'])
def doc(endpoint):
	config = get_config(endpoint)
	return render_template('index.html', endpoints=[_doc(config, endpoint)])


def main():
	args = parse_args()

	app.config.from_pyfile(os.path.abspath(args.config))
	app.debug = args.debug

	errors = check_config(app.config)
	if errors:
		for error in errors:
			app.logger.error(error)
		sys.exit(1)

	app.run(host=args.host, port=args.port)


if __name__ == '__main__':
	main()
