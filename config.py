from sys import argv

DEFAULT_CONFIG = {
	'DEBUG' : False,
	'DATABASE' : r'./worddb.sqlite',
	'LAST_RESULT_PATH' : r'./lastSrchResult.json',
	'BORDER_WIDTH' : 1,
	'CORNER_RADIUS' : 3.5,
	'BTN_WIDTH' : 64,
	'BORDER_COLOR' : (0.0, 0.47843137254901963, 1.0, 1.0),
	'FONT_COLOR' : (0.0, 0.47843137254901963, 1.0, 1.0),
}

DEVELOPMENT_CONFIG = {
	'DEBUG' : False,
	'DATABASE' : r'./test/testdb.sqlite',
	'LAST_RESULT_PATH' : r'./test/lastSrchResult.json',
}

class Config(dict):

	def __init__(self):
		self.update(DEFAULT_CONFIG)
		if len(argv) > 1:
			run_opt = argv[1]
			if run_opt == '--dev' or '--development':
				self.update(DEVELOPMENT_CONFIG)

appconfig = Config()
