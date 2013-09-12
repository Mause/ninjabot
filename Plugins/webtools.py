from __future__ import unicode_literals
from apis.BeautifulSoup import BeautifulSoup as bs, BeautifulStoneSoup as bss, Tag
from apis import googl
import re
import urllib
import requests

#I'm silencing all errors from webtools' autochecker, simply because there are so many that could pop up.
#/me is lazy

class Plugin:
    def __init__(self, controller, language):
        self.c = controller
        self.lang = language
        # Yeah, the bot is a chrome browser, ok? I'M NOT LYING, I SWEAR!
        self.useragent = 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.60 Safari/537.1'


    def sizeof_fmt(self, num):
        for x in ['bytes','KB','MB','GB','TB']:
            if num < 1024.0:
                return "{:3.1f}{}".format(num, x)
            num /= 1024.0

    def tag2string(self, tag, keep_bold=False):
        if tag.string is None:
            ret = ''
            for item in tag.contents:
                if isinstance(item, Tag):
                    if keep_bold and item.name == 'b':
                        ret += '\002'
                        ret += self.tag2string(item)
                        ret += '\002'
                    else:
                        ret += self.tag2string(item)
                else:
                    ret += item
            return ret
        else:
            return tag.string

    def fix_text(self, text):
        soup = bs(text, convertEntities=bs.HTML_ENTITIES)
        return self.tag2string(soup, keep_bold=True)



    def on_incoming(self, msg):
        if not msg.type == msg.CHANNEL:
            return
        if self.c.is_ignored(msg.nick):
            return

        try:
            urls = re.findall(r'https?://[-A-Za-z0-9+&@#/%?=~_()|!:,.;]*[-A-Za-z0-9+&@#/%=~_()|]', msg.body)
            for url in urls:
                if url.startswith('(') and url.endswith(')'):
                    url = url[1:-1]

                filename = re.search(r'/([^/]+)/?$', url).groups(1)[0]

                req_headers = {}
                if self.lang:
                    req_headers['Accept-Language'] = self.lang

                head = requests.head(url)
                content_type = head.headers['content-type']

                if 'text/html' in content_type:
                    req = requests.get(url, headers=req_headers, timeout=5)
                    e = re.search(r'''<\s*meta\s[^>]+?charset=([^>]*?)[;'">]''', req.text, re.I)
                    if e:
                        req.encoding = e.group(1)
                    r = re.search(r'<(title|h1)>(.*?)</\1>', req.text, re.I)
                    if r is None:
                        return
                    title = r.group(2).strip().replace('\n', '')
                    title = self.fix_text(title)
                    message = 'Title: ' + title
                else:
                    content_length = head.headers.get('content-length','')
                    if content_length.isdigit():
                        size = self.sizeof_fmt(int(content_length))
                    else:
                        size = "Unknown size"
                    message = '{}: {} ({})'.format(filename, content_type, size)
                self.c.privmsg(msg.channel, message)
        except Exception as e:
            print 'EXCEPTION!'
            print type(e), e.args, e.message


    def trigger_w(self, msg):
        "Usage: w <search term>. Prints a short description of the corresponding wikipedia article."
        if len(msg.args) == 0:
            self.c.notice(msg.nick, "Please specify a search term")
            return

        params = {'action': 'opensearch',
                  'format': 'xml',
                  'limit' : '2',
                  'search': ' '.join(msg.args)}

        resp = bss(requests.post("http://en.wikipedia.org/w/api.php", data=params).text, convertEntities=bs.HTML_ENTITIES)

        if resp.textTag:
            index = 1 if 'may refer to:' in resp.descriptionTag.string else 0
            info = resp.findAll('description')[index].string.strip()
            url = resp.findAll('url')[index].string
            message = u"\002Wikipedia ::\002 {} \002::\002 {}".format(info, googl.get_short(url,self.c.config))
            self.c.privmsg(msg.channel, message)
        else:
            self.c.privmsg(msg.channel, '{}: No articles were found.'.format(' '.join(msg.args)))

    def trigger_wiki(self, msg):
        "Usage: wiki <search term>. Prints a short description of the corresponding wikipedia article."
        self.trigger_w(msg)

    def trigger_g(self, msg):
        "Usage: g <search term>. Prints title & short description of first google result."
        if len(msg.args) == 0:
            self.c.notice(msg.nick, "Please specify a search term")
            return

        url = 'http://ajax.googleapis.com/ajax/services/search/web'
        params = {'q': ' '.join(msg.args),
                  'v': 1.0}
        resp_json = requests.get(url, params=params).json()

        results = resp_json["responseData"]["results"]
        if len(results) == 0:
            self.c.privmsg(msg.channel, '{}: No results.'.format(' '.join(msg.args)))
            return
        top_res = results[0]

        print(top_res)
        url     = googl.get_short(top_res['url'], self.c.config)
        content = self.fix_text(top_res['content'])
        title   = self.fix_text(top_res['title'])

        message = u"\002\0032G\0034o\0038o\0032g\0033l\0034e\003 ::\002 {} \002::\002 {} \002::\002 {}".format(
            title,
            content,
            url)
        self.c.privmsg(msg.channel, message)


    def trigger_yt(self, msg):
        "Usage: yt <searchterm>. Prints title and link to first youtube result."
        if len(msg.args) == 0:
            self.c.notice(msg.nick, "Please specify a search term")
            return

        url = "https://gdata.youtube.com/feeds/api/videos"
        params = {'q'          : ' '.join(msg.args),
                  'max-results': '1',
                  'v'          : '2',
                  'alt'        : 'json'}
        req = requests.get(url, params=params)
        req_json = req.json()
        if 'entry' not in req_json['feed']:
            self.c.privmsg(msg.channel, '{}: No entries were found.'.format(' '.join(msg.args)))
            return

        entry = req_json['feed']['entry']
        entry = entry[0]
        link  = entry['link'][0]
        title = self.fix_text(entry['title']['$t'])
        desc  = self.fix_text(entry['media$group']['media$description']['$t'])

        message = u"\002You\0030,4Tube\003 ::\002 {} \002::\002 {} \002::\002 {}".format(
            title,
            desc,
            "http://youtu.be/"+entry['id']['$t'].split(':')[-1],)
        self.c.privmsg(msg.channel, message)


    def trigger_ud(self, msg):
        "Usage: ud <search term>. Prints first UrbanDictionary result."
        if len(msg.args) == 0:
            self.c.notice(msg.nick, "Please specify a search term")
            return

        url = "http://www.urbandictionary.com/define.php"
        data = {'term': ' '.join(msg.args)}
        soup = bs(requests.post(url,data=data).text, convertEntities=bs.HTML_ENTITIES)
        word = soup.find('td', 'word')
        if not word:
            self.c.privmsg(msg.channel, '{}: No entries were found.'.format(' '.join(msg.args)))
            return

        word = self.tag2string(word).strip()
        defi = self.tag2string(soup.find('div', 'definition')).split('<br')[0]
        self.c.privmsg(msg.channel, '{}: {}'.format(word, defi))

    def trigger_tx(self, msg):
        "Usage: tx <expression>. Prints a link to a graphical representation of the supplied LaTeX expression."

        url = "http://www.texify.com/${}$".format(urllib.quote(' '.join(msg.args)))
        self.c.privmsg(msg.channel, 'LaTeX :: {}'.format(googl.get_short(url, self.c.config)))

