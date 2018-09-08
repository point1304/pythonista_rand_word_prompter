import appex, console, requests, sys, os, sqlite3, webbrowser
from urllib.parse import quote

from bs4 import BeautifulSoup

import config

class Config(dict):

	def __init__(self):
		if len(sys.argv) > 1:
			run_opt = sys.argv[1]
			if run_opt == '--dev' or '--development':
				self.from_mapping(config.DEVELOPMENT_CONFIG)
		else:
			self.from_mapping(config.DEFAULT_CONFIG)
			
	def from_mapping(self, mapping):
		if not all((el == el.upper() for el in mapping.keys())):
			raise KeyError("a :inst:Config doesn't accept non-upper keys")
		self.update(mapping)

def _get_db():
	config = Config()
	path = config['DATABASE']
	if not os.path.exists(path):
		if not os.path.exists(os.path.dirname(path)):
			os.makedirs(os.path.dirname(path))
		db = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
		with open(r'./initdb.sql', 'r', encoding='utf-8') as f:
			db.executescript(f.read())
			db.commit()
	else:
		db = sqlite3.connect(path,
		detect_types=sqlite3.PARSE_DECLTYPES)
	return db

def query_join(base_url, query):
	qry_str = ''
	for key, value in query.items():
		qry_str += '='.join((key, value)) + '&'
	return base_url + '?' + qry_str[0:-1]
	
def fetch_jpdic(word_input):
	query = {
		'q' : quote(word_input),
	}
	base_url = 'https://ja.dict.naver.com/search.nhn'
	target_url = query_join(base_url, query)
	req = requests.get(target_url)
	soup = BeautifulSoup(req.text, 'html5lib')
	def to_str(el):
		return el.text.strip().replace('\xa0', ' ')
	word, meaning = [], []
	sel = soup.select('div.section.all.section_word > div.srch_box')
	for el in sel:
		word_sel = el.select('p.entry')
		if word_sel:
			word.append(to_str(*word_sel))
			
			meaning_sel = el.select('span.lst_txt')
			if len(meaning_sel) > 1:
				meaning_pack = ''
				i = 1
				for meaning_el in meaning_sel:
					meaning_pack += str(i) + '. ' + to_str(meaning_el) + '\n'
					i += 1
				meaning.append(meaning_pack)
			elif len(meaning_sel) == 1:
				meaning.append(to_str(*meaning_sel))
			else: meaning.append('')
			
	return target_url, tuple(word), tuple(meaning)
	
def insert_to_db(word):
	target_url, child_words, meanings = fetch_jpdic(word)
	conn = _get_db()
	c = conn.cursor()
	c.execute("SELECT jp_word FROM jp_parent_word WHERE jp_word = ?", (word,))
	prev_word = c.fetchone()
	if child_words and prev_word is None:
		reply = console.alert('Question', 
			'Do you want to save\nthe fetched result into the db?',
			'はい', 'いいえ', hide_cancel_button=True)
		if reply == 1:
			conn = _get_db()
			c = conn.cursor()
			c.execute("INSERT INTO jp_parent_word (jp_word) VALUES (?)", (word,))

			for i in range(len(child_words)):
				c.execute("INSERT INTO jp_child_word (jp_parent_word, jp_child_word, jp_meaning) VALUES (?, ?, ?)", (word, child_words[i], meanings[i]))
	
	webbrowser.open_new('safari-' + target_url)
	c.close()
	conn.commit()
	conn.close()

def ext_main():
	text = appex.get_text()
	if text is None:
		return
	insert_to_db(text)

def shortcut_main():
	text = console.input_alert('辞書検索',
		'検索するキーワードをご入力してください')
	while not text:
		text = console.input_alert('辞書検索', '入力ありません。検索する単語をご入力してください')
		if not text:
			continue
		else:
			break
	
	insert_to_db(text)

if appex.is_running_extension():
	ext_main()
	del console, requests, sys, os, sqlite3, BeautifulSoup, config
	appex.finish()
	del appex
	
else:
	shortcut_main()
	del console, requests, sys, os, sqlite3, BeautifulSoup, config, appex
