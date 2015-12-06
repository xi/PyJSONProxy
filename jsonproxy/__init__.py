from __future__ import absolute_import

import os
import sys
import argparse

from flask import Flask

from .api import api
from .lib import check_config


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
