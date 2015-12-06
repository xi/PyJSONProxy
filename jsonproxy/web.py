"""Flask inspired wrapper around aiohttp."""

from functools import lru_cache
from pkg_resources import resource_filename
import asyncio
import logging
import os

from aiohttp import web
import jinja2


@lru_cache()
def get_template(name):
	path = resource_filename(__name__, os.path.join('templates', name))
	with open(path) as fh:
		return jinja2.Template(fh.read())


def render_template(name, **kwargs):
	template = get_template(name)
	text = template.render(**kwargs)
	return web.Response(body=text.encode('utf8'))


def jsonify(data, **kwargs):
	return web.json_response(data, **kwargs)


def abort(code):
	if code == 404:
		raise web.HTTPNotFound
	elif code >= 500:
		raise web.HTTPInternalServerError
	else:
		raise web.HTTPBadRequest


def make_response(data, **kwargs):
	if isinstance(data, web.StreamResponse):
		return data
	elif isinstance(data, str):
		return web.Response(body=data.encode('utf8'), **kwargs)
	elif isinstance(data, bytes):
		return web.Response(body=data, **kwargs)
	else:
		raise TypeError('cannot make response from {}'.format(data))


class Application:
	def __init__(self, name):
		self.name = name
		self.loop = asyncio.get_event_loop()
		self.app = web.Application(loop=self.loop)
		self.logger = logging
		self.config = {}
		self.debug = False  # NOTE: does not do anything yet

	def config_from_file(self, path):
		with open(path) as fh:
			exec(compile(fh.read(), path, 'exec'), self.config)

	def add_route(self, path, fn, methods=('GET',)):
		@asyncio.coroutine
		def wrapped(*args, **kwargs):
			data = yield from asyncio.async(fn(*args, **kwargs))
			return make_response(data)

		for method in methods:
			self.app.router.add_route(method, path, wrapped)

	def route(self, path, methods=('GET',)):
		def decorator(fn):
			self.add_route(path, fn, methods=methods)
			return fn
		return decorator

	def run(self, host='localhost', port=5000):
		server = self.loop.create_server(self.app.make_handler(), host, port)
		self.loop.run_until_complete(server)
		self.logger.info("Server started at http://{}:{}".format(host, port))
		try:
			self.loop.run_forever()
		except KeyboardInterrupt:
			pass
