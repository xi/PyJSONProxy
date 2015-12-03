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

api = Blueprint('api', __name__, static_folder='static')


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


def get_attribute_list(html, selector):
	s = selector.rsplit('@', 1)[0]
	if s:
		elements = html.select(s)
	else:
		elements = [html]

	if '@' in selector:
		attr = selector.rsplit('@', 1)[1]
		return [element[attr] for element in elements]
	else:
		return [element.text.strip() for element in elements]


def get_attribute(html, selector):
	l = get_attribute_list(html, selector)
	if len(l) > 0:
		return l[0]


def get_fields(html, config):
	data = {}
	for key, value in config['fields'].items():
		if isinstance(value, str):
			data[key] = get_attribute(html, value)
		elif 'fields' in value:
			elements = html.select(value['selector'])
			data[key] = [get_fields(e, value) for e in elements]
		else:
			data[key] = get_attribute_list(html, value['selector'])
	return data


def scrape(url, config):
	html = urlopen(url, parse=True)
	data = get_fields(html, config)
	data['url'] = url
	return jsonify(data)


def proxy(url, config):
	return make_response(*urlopen(url))


@api.route('/<endpoint>/<path:path>', methods=['GET'])
def main(endpoint, path):
	try:
		config = current_app.config['ENDPOINTS'][endpoint]
	except KeyError:
		abort(404)

	url = request.url.replace(request.host_url + endpoint + '/', config['host'])

	if 'fields' in config:
		response = scrape(url, config)
	else:
		response = proxy(url, config)

	if current_app.config.get('ALLOW_CORS', False):
		response.headers['Access-Control-Allow-Origin'] = '*'

	return response


def _fields_doc(config):
	if isinstance(config, dict):
		fields = config.get('fields', {})
		doc = config.get('fields_doc', {})
		for key in fields:
			yield key, doc.get(key, ''), list(_fields_doc(fields[key]))


def _doc(endpoint):
	config = current_app.config['ENDPOINTS'][endpoint]

	data = {
		'title': endpoint,
		'doc': config.get('doc', ''),
		'fields': list(_fields_doc(config)),
	}

	data['fields'].append(('url', 'url of the scraped page', []))

	return data


@api.route('/', methods=['GET'])
def index():
	data = [_doc(endpoint) for endpoint in current_app.config['ENDPOINTS']]
	return render_template('index.html', endpoints=data)


@api.route('/<endpoint>/', methods=['GET'])
def doc(endpoint):
	if endpoint not in current_app.config['ENDPOINTS']:
		abort(404)
	return render_template('index.html', endpoints=[_doc(endpoint)])
