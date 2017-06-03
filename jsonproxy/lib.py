import argparse

from bs4 import BeautifulSoup

try:
	from functools import lru_cache
except ImportError:
	from cachetools import lru_cache

ENDPOINTS = 'ENDPOINTS'


def iter_attribute(html, selector):
	optional = selector.endswith('?')
	if optional:
		selector = selector[:-1]

	s = selector.rsplit('@', 1)[0]
	if s:
		elements = html.select(s)
	else:
		elements = [html]

	if '@' in selector:
		attr = selector.rsplit('@', 1)[1]
		if optional:
			return (element.get(attr) for element in elements)
		else:
			return (element[attr] for element in elements)
	else:
		return (element.text.strip() for element in elements)


def get_attribute(html, selector):
	l = iter_attribute(html, selector)
	try:
		return next(l)
	except StopIteration:
		if not selector.endswith('?'):
			raise


def get_fields(html, config):
	data = {}
	for key, value in config['fields'].items():
		if isinstance(value, str):
			data[key] = get_attribute(html, value)
		elif 'fields' in value:
			elements = html.select(value['selector'])
			data[key] = [get_fields(e, value) for e in elements]
		else:
			data[key] = list(iter_attribute(html, value['selector']))
	return data


@lru_cache()
def parse_html(body):
	return BeautifulSoup(body)


def scrape(url, body, config):
	html = parse_html(body)
	data = get_fields(html, config)
	data['url'] = url
	if 'post' in config:
		data = config['post'](data)
	return data


def _fields_doc(config):
	if isinstance(config, dict):
		fields = config.get('fields', {})
		doc = config.get('fields_doc', {})
		for key in fields:
			yield key, doc.get(key, ''), list(_fields_doc(fields[key]))


def _doc(config, endpoint):
	data = {
		'title': endpoint,
		'doc': config.get('doc', ''),
		'fields': list(_fields_doc(config)),
	}

	data['fields'].append(('url', 'url of the scraped page', []))

	return data


def check_fields_config(fields, endpoint, field=''):
	for key, value in fields.items():
		full_key = field + '.' + key if field else key
		if isinstance(value, dict):
			if 'selector' not in value:
				yield ('No selector configured for field %s in endpoint %s.' %
					(full_key, endpoint))
			if 'fields' in value:
				for error in check_fields_config(value['fields'], endpoint, full_key):
					yield error


def check_config(config):
	errors = []

	if ENDPOINTS not in config or len(config[ENDPOINTS]) == 0:
		errors.append('No endpoints configured.')
	else:
		for key, data in config[ENDPOINTS].items():
			if 'fields' in data:
				if len(data['fields']) == 0:
					errors.append('No fields configured for endpoint %s.' % key)
				else:
					errors += list(check_fields_config(data['fields'], key))

	return errors


def parse_args():
	parser = argparse.ArgumentParser(description='simple proxy and scraper')
	parser.add_argument('config')
	parser.add_argument('-d', '--debug', action='store_true')
	parser.add_argument('-p', '--port', type=int, default=5000)
	parser.add_argument('-H', '--host', default='localhost')
	return parser.parse_args()
