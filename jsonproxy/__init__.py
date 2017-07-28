from functools import lru_cache
from pkg_resources import resource_filename
import argparse
import asyncio
import os
import sys

from aiohttp import web
import aiohttp
import jinja2

from .lib import check_config
from .lib import _doc
from .lib import ENDPOINTS
from .lib import scrape

__version__ = '2.0.0'

CONFIG = {}


def get_config(endpoint):
	try:
		return CONFIG[ENDPOINTS][endpoint]
	except KeyError:
		raise aiohttp.web_exceptions.HTTPNotFound


@lru_cache()
def get_template(name):
	local_path = os.path.join('templates', name)
	path = resource_filename(__name__, local_path)
	with open(path) as fh:
		s = fh.read()
		return jinja2.Template(s)


def render_template(name, **kwargs):
	"""Shortcut for rendering a jinja template to a response."""
	template = get_template(name)
	text = template.render(**kwargs)
	return web.Response(
		body=text.encode('utf8'),
		content_type='text/html')


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
	print('{}:{}'.format(method, url))
	async with aiohttp.request(method, url) as response:
		if response.status == 404:
			raise aiohttp.web_exceptions.HTTPNotFound
		response.raise_for_status()
		# get response before closing the connection
		await response.read()
		return response


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
		data = scrape(url, body, config)
		response = web.json_response(data, status=remote.status)

	if CONFIG.get('ALLOW_CORS', False):
		response.headers['Access-Control-Allow-Origin'] = '*'

	return response


def index(request):
	config = CONFIG[ENDPOINTS]
	data = [_doc(config[endpoint], endpoint) for endpoint in config]
	return render_template('index.html', endpoints=data)


def doc(request):
	endpoint = request.match_info['endpoint']
	config = get_config(endpoint)
	data = [_doc(config, endpoint)]
	return render_template('index.html', endpoints=data)


def parse_args():
	parser = argparse.ArgumentParser(description='simple proxy and scraper')
	parser.add_argument('config')
	parser.add_argument('--version', action='version', version=__version__)
	parser.add_argument('-d', '--debug', action='store_true')
	parser.add_argument('-p', '--port', type=int, default=5000)
	parser.add_argument('-H', '--host', default='localhost')
	return parser.parse_args()


def main():
	args = parse_args()

	config_path = os.path.abspath(args.config)
	with open(config_path) as fh:
		exec(compile(fh.read(), config_path, 'exec'), CONFIG)  # nosec

	errors = check_config(CONFIG)
	if errors:
		for error in errors:
			print(error)
		sys.exit(1)

	loop = asyncio.get_event_loop()
	app = web.Application(loop=loop)

	app.router.add_route('GET', '/', index)
	app.router.add_route('GET', '/{endpoint}/', doc)
	app.router.add_route('GET', '/{endpoint}/{path:.+}', handle)

	h = app.make_handler()
	f = loop.create_server(h, args.host, args.port)
	srv = loop.run_until_complete(f)
	msg = "Running on http://{}:{}/ (Press CTRL+C to quit)"
	print(msg.format(args.host, args.port))

	try:
		loop.run_forever()
	except KeyboardInterrupt:
		pass
	finally:
		loop.run_until_complete(h.finish_connections(1.0))
		srv.close()
		loop.run_until_complete(srv.wait_closed())
		loop.run_until_complete(app.cleanup())

	loop.close()


if __name__ == '__main__':
	main()
