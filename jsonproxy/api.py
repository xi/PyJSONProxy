try:
	from urllib.request import urlopen
	from urllib.error import HTTPError
except ImportError:
	from urllib2 import urlopen
	from urllib2 import HTTPError

from flask import Blueprint
from flask import request
from flask import current_app
from flask import abort
from flask import jsonify

from bs4 import BeautifulSoup

api = Blueprint('api', __name__, static_folder='static')


def get_attribute_list(html, selector):
	if '@' in selector:
		s, attr = selector.rsplit('@', 1)
		return [element[attr] for element in html.select(s)]
	else:
		return [element.text.strip() for element in html.select(selector)]


def get_attribute(html, selector):
	return get_attribute_list(html, selector)[0]


@api.route('/', methods=['GET'])
def main():
	return jsonify()


@api.route('/<endpoint>/<path:path>', methods=['GET'])
def proxy(endpoint, path):
	try:
		config = current_app.config['ENDPOINTS'][endpoint]
	except KeyError:
		abort(404)

	try:
		url = request.url.replace(request.host_url + endpoint + '/', config['host'])
		current_app.logger.info('fetching %s' % url)
		original = urlopen(url)
	except HTTPError as error:
		abort(error.code)

	body = original.read()
	code = original.getcode()
	headers = original.headers.items()

	if config['type'] == 'scrape_item':
		html = BeautifulSoup(body)
		data = {
			'url': url
		}
		for key, selector in config['fields'].items():
			data[key] = get_attribute(html, selector)
		response = jsonify(data)
	elif config['type'] == 'scrape_list':
		html = BeautifulSoup(body)
		response = jsonify({
			'url': url,
			'l': get_attribute_list(html, config['selector'])
		})
	else:
		response = make_response(body, code, headers)

	if current_app.config.get('ALLOW_CORS', False):
		response.headers['Access-Control-Allow-Origin'] = '*'

	return response
