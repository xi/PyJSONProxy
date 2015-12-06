from __future__ import absolute_import

import os
import sys

from flask import Flask

from .api import api
from .lib import parse_args
from .lib import check_config


def main():
	args = parse_args()

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
