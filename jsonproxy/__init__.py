import asyncio
import os
import sys

import aiohttp
from aiohttp import web
from bs4 import BeautifulSoup

from .web import Application
from .web import jsonify
from .web import render_template
from .web import make_response
from .web import abort

from .lib import check_config
from .lib import _doc
from .lib import ENDPOINTS
from .lib import parse_args
from .lib import scrape

app = Application(__name__)


def get_config(endpoint):
	try:
		return app.config[ENDPOINTS][endpoint]
	except KeyError:
		abort(404)


def async_cache(maxsize=128):
	cache = {}

	def decorator(fn):
		def wrapper(*args):
			key = ':'.join(args)
			if key not in cache:
				if len(cache) >= maxsize:
					del cache[cache.keys().next()]
				cache[key] = yield from fn(*args)
			return cache[key]
		return wrapper
	return decorator


@async_cache()
def _request(method, url):
	app.logger.info(method, url)
	print(method, url)
	response = yield from aiohttp.request(method, url)
	if response.status != 200:
		abort(response.status)
	else:
		return response


@app.route('/{endpoint}/{path:.+}', methods=['GET', 'HEAD', 'OPTIONS'])
@asyncio.coroutine
def handle(request):
	endpoint = request.match_info['endpoint']

	config = get_config(endpoint)
	url = config['host'] + request.match_info['path']
	if request.query_string:
		url += '?' + request.query_string

	remote = yield from _request(request.method, url)
	body = yield from remote.read()

	if 'fields' in config and request.method == 'GET':
		response = jsonify(scrape(url, body, config), status=remote.status)
	else:
		response = make_response(body, status=remote.status)

	if app.config.get('ALLOW_CORS', False):
		response.headers['Access-Control-Allow-Origin'] = '*'

	return response


@app.route('/')
def index(request):
	config = app.config[ENDPOINTS]
	data = [_doc(config[endpoint], endpoint) for endpoint in config]
	return render_template('index.html', endpoints=data)


@app.route('/{endpoint}/')
def doc(request):
	endpoint = request.match_info['endpoint']
	config = app.get_config(endpoint)
	data = [_doc(config, endpoint)]
	return render_template('index.html', endpoints=data)


def main():
	args = parse_args()

	app.config_from_file(os.path.abspath(args.config))
	app.debug = args.debug

	errors = check_config(app.config)
	if errors:
		for error in errors:
			app.logger.error(error)
		sys.exit(1)

	app.run(host=args.host, port=args.port)


if __name__ == '__main__':
	main()
