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
	if '@' in selector:
		s, attr = selector.rsplit('@', 1)
		return [element[attr] for element in html.select(s)]
	else:
		return [element.text.strip() for element in html.select(selector)]


def get_attribute(html, selector):
	return get_attribute_list(html, selector)[0]


def scrape_item(url, config):
	tree = urlopen(url, parse=True)
	data = {
		'url': url
	}
	for key, selector in config['fields'].items():
		data[key] = get_attribute(tree, selector)
	return jsonify(data)


def scrape_list(url, config):
	tree = urlopen(url, parse=True)
	return jsonify({
		'url': url,
		'l': get_attribute_list(tree, config['selector'])
	})


def proxy(url, config):
	return make_response(*urlopen(url))


@api.route('/<endpoint>/<path:path>', methods=['GET'])
def main(endpoint, path):
	try:
		config = current_app.config['ENDPOINTS'][endpoint]
	except KeyError:
		abort(404)

	url = request.url.replace(request.host_url + endpoint + '/', config['host'])
	_type = config.get('type', 'proxy')

	if _type == 'scrape_item':
		response = scrape_item(url, config)
	elif _type == 'scrape_list':
		response = scrape_list(url, config)
	else:
		response = proxy(url, config)

	if current_app.config.get('ALLOW_CORS', False):
		response.headers['Access-Control-Allow-Origin'] = '*'

	return response


def _doc(endpoint):
	config = current_app.config['ENDPOINTS'][endpoint]
	url_doc = 'url of the scraped page'

	data = {
		'title': endpoint,
		'doc': config.get('doc', ''),
		'type': config.get('type', 'proxy'),
		'fields': [],
	}

	if data['type'] == 'scrape_item':
		fields_doc = config.get('fields_doc', {})
		data['fields'].append(('url', url_doc))
		for key in config['fields']:
			doc = fields_doc.get(key, '')
			data['fields'].append((key, doc))

	if data['type'] == 'scrape_list':
		data['fields'] = [
			('url', url_doc),
			('l', 'list of results'),
		]

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
