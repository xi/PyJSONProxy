from __future__ import absolute_import

import os
import sys

from flask import Flask
from flask.helpers import find_package

from .api import api

TYPES = ['proxy', 'scrape_item', 'scrape_list']
ENDPOINTS = 'ENDPOINTS'


def etc_path(app):  # pragma: no cover
	prefix, package_path = find_package(app.import_name)
	if prefix is None:
		return os.path.join(package_path, 'etc')
	return os.path.join(prefix, 'etc')


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


def create_app(name, settings_override=None):  # pragma: no cover
	app = Flask(name)

	app.config.from_pyfile(os.path.join(etc_path(app), 'settings.cfg'))
	app.config.from_object(settings_override)

	errors = check_config(app.config)
	if errors:
		for error in errors:
			app.logger.error(error)
		sys.exit(1)

	app.register_blueprint(api)

	return app


def main():
	app = create_app(__name__)
	app.run()


if __name__ == '__main__':
	main()
