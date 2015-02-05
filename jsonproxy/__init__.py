from __future__ import absolute_import

import os
import sys
import argparse

from flask import Flask

from .api import api

TYPES = ['proxy', 'scrape_item', 'scrape_list']
ENDPOINTS = 'ENDPOINTS'


def check_config(config):
	errors = []

	if ENDPOINTS not in config or len(config[ENDPOINTS]) == 0:
		errors.append('No endpoints configured.')
	else:
		for key, data in config[ENDPOINTS].items():
			_type = data.get('type', 'proxy')
			if _type not in TYPES:
				errors.append('Unknown endpoint type %s for endpoint %s. '
					'Choose one of %s.' % (_type, key, ', '.join(TYPES)))
			elif _type == 'scrape_item':
				if 'fields' not in data or len(data['fields']) == 0:
					errors.append('No fields configured for endpoint %s of type %s.' %
						(key, _type))
			elif _type == 'scrape_list':
				if 'selector' not in data:
					errors.append('Endpoint %s of type %s is missing a selector.' %
						(key, _type))

	return errors


def main():
	parser = argparse.ArgumentParser(description='simple proxy and scraper')
	parser.add_argument('config')
	parser.add_argument('-d', '--debug', action='store_true')
	parser.add_argument('-p', '--port', type=int)
	parser.add_argument('-H', '--host')
	args = parser.parse_args()

	app = Flask(__name__)
	app.config.from_pyfile(os.path.abspath(args.config))

	errors = check_config(app.config)
	if errors:
		for error in errors:
			app.logger.error(error)
		sys.exit(1)

	app.register_blueprint(api)
	app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
	main()
