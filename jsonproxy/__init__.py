import argparse
import os
import sys

import aiohttp

from fakes import Fakes
from fakes import jsonify
from fakes import make_response
from fakes import abort

from .lib import check_config
from .lib import _doc
from .lib import ENDPOINTS
from .lib import scrape

app = Fakes(__name__)


def get_config(endpoint):
	try:
		return app.config[ENDPOINTS][endpoint]
	except KeyError:
		abort(404)


def async_cache(maxsize=128):
	cache = {}

	def decorator(fn):
		async def wrapper(*args):
			key = ':'.join(args)
			if key not in cache:
				if len(cache) >= maxsize:
					del cache[cache.keys().next()]
				cache[key] = await fn(*args)
			return cache[key]
		return wrapper
	return decorator


@async_cache()
async def _request(method, url):
	app.logger.info('{}:{}'.format(method, url))
	async with aiohttp.request(method, url) as response:
		if response.status != 200:
			abort(response.status)
		else:
			# get response before closing the connection
			await response.read()
			return response


@app.route('/{endpoint}/{path:.+}')
async def handle(request):
	endpoint = request.match_info['endpoint']

	config = get_config(endpoint)
	if '{' in config['host']:
		parts = request.match_info['path'].strip('/').split('/')
		url = config['host'].format(*parts)
	else:
		url = config['host'] + request.match_info['path']
	if request.query_string:
		url += '?' + request.query_string

	remote = await _request(request.method, url)
	body = await remote.read()

	if 'fields' in config:
		response = jsonify(scrape(url, body, config), status=remote.status)

	if app.config.get('ALLOW_CORS', False):
		response.headers['Access-Control-Allow-Origin'] = '*'

	return response


@app.route('/')
def index(request):
	config = app.config[ENDPOINTS]
	data = [_doc(config[endpoint], endpoint) for endpoint in config]
	return app.render_template('index.html', endpoints=data)


@app.route('/{endpoint}/')
def doc(request):
	endpoint = request.match_info['endpoint']
	config = get_config(endpoint)
	data = [_doc(config, endpoint)]
	return app.render_template('index.html', endpoints=data)


def parse_args():
	parser = argparse.ArgumentParser(description='simple proxy and scraper')
	parser.add_argument('config')
	parser.add_argument('-d', '--debug', action='store_true')
	parser.add_argument('-p', '--port', type=int, default=5000)
	parser.add_argument('-H', '--host', default='localhost')
	return parser.parse_args()


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
