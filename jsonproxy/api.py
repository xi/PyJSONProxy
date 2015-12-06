from __future__ import absolute_import

try:
	from urllib.request import urlopen as _urlopen
	from urllib.error import HTTPError
except ImportError:
	from urllib2 import urlopen as _urlopen
	from urllib2 import HTTPError

from flask import Blueprint
from flask import request
from flask import current_app
from flask import abort
from flask import jsonify
from flask import make_response
from flask import render_template
from bs4 import BeautifulSoup
import cachetools

from .lib import get_fields
from .lib import _doc
from .lib import ENDPOINTS

api = Blueprint('api', __name__, static_folder='static')


def get_config(endpoint):
	try:
		return current_app.config[ENDPOINTS][endpoint]
	except KeyError:
		abort(404)


@cachetools.ttl_cache()
def urlopen(url, parse=False):
	try:
		current_app.logger.info('fetching %s' % url)
		original = _urlopen(url)

		body = original.read()
		code = original.getcode()
		headers = original.headers.items()

		if parse:
			return BeautifulSoup(body)
		else:
			return body, code, headers
	except HTTPError as error:
		abort(error.code)


def scrape(url, config):
	html = urlopen(url, parse=True)
	data = get_fields(html, config)
	data['url'] = url
	if 'post' in config:
		data = config['post'](data)
	return jsonify(data)


def proxy(url, config):
	return make_response(*urlopen(url))


@api.route('/<endpoint>/<path:path>', methods=['GET'])
def main(endpoint, path):
	config = get_config(endpoint)
	url = request.url.replace(request.host_url + endpoint + '/', config['host'])

	if 'fields' in config:
		response = scrape(url, config)
	else:
		response = proxy(url, config)

	if current_app.config.get('ALLOW_CORS', False):
		response.headers['Access-Control-Allow-Origin'] = '*'

	return response


@api.route('/', methods=['GET'])
def index():
	config = current_app.config[ENDPOINTS]
	data = [_doc(config[endpoint], endpoint) for endpoint in config]
	return render_template('index.html', endpoints=data)


@api.route('/<endpoint>/', methods=['GET'])
def doc(endpoint):
	config = get_config(endpoint)
	return render_template('index.html', endpoints=[_doc(config, endpoint)])
