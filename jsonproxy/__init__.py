from __future__ import absolute_import

import os
import sys
import argparse

from flask import Flask

from .api import api

ENDPOINTS = 'ENDPOINTS'


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


def main():
	parser = argparse.ArgumentParser(description='simple proxy and scraper')
	parser.add_argument('config')
	parser.add_argument('-d', '--debug', action='store_true')
	parser.add_argument('-p', '--port', type=int)
	parser.add_argument('-H', '--host')
	args = parser.parse_args()

	app = Flask(__name__)
	app.config.from_pyfile(os.path.abspath(args.config))
	app.debug = args.debug

	errors = check_config(app.config)
	if errors:
		for error in errors:
			app.logger.error(error)
		sys.exit(1)

	app.register_blueprint(api)
	app.run(host=args.host, port=args.port)


if __name__ == '__main__':
	main()
