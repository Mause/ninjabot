from urllib.request import urlopen
from urllib.parse import urlencode
import json

class Paste(object):
	def write(self, string, private=True, expire=3600):
		"""
		Write <string> to a new kdepaste
		Returns kdepaste URL or error message
		"""

		url = 'http://paste.kde.org/'
		args = {
			'paste_data': string,
			'paste_lang': 'text',
			'api_submit': 'true',
			'mode': 'json',

			'paste_private': 'yes' if private else 'no',
			'paste_expire': expire
		}
		post_data = urlencode(args).encode('utf-8')

		u = urlopen(url, post_data).read().decode('utf-8')
		j = json.loads(u)['result']

		if 'error' in j.keys():
			return j['error']

		o = ''
		if private:
			o = 'http://pastebin.kde.org/{:s}/{:s}'.format(j['id'], j['hash'])

		return o


APIS = {
	# Making an instance to preserve old API
	'core.paste': Paste()
}
