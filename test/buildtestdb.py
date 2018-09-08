import requests, sqlite3
from bs4 import BeautifulSoup
from urllib.parse import quote


def query_join(base_url, query):
	qry_str = ''
	for key, value in query.items():
		qry_str += '='.join((key, value)) + '&'
	
	return base_url + '?' + qry_str[0:-1]
	
	
def fetch_endic(word_input):
	""" ENDIC VERSION
	query = {
		'sLn' : 'kr',
		'isOnlyViewEE' : 'N',
		'searchOption' : 'entry_idiom',
		'query' : quote(word_input),
	}
	base_url = 'https://endic.naver.com/search.nhn'
	"""
	#: JPDIC VERSION
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
			
	return tuple(word), tuple(meaning)
	
def init_db():
	conn = sqlite3.connect(r'./worddb.sqlite', detect_types=sqlite3.PARSE_DECLTYPES)
	with open(r'./initdb.sql', 'r') as f:
		conn.executescript(f.read())
	
	return conn

def main(search_list):	
	conn = init_db()
	c = conn.cursor()
	for word in search_list:
		print(word)
		child_words, meanings = fetch_endic(word)
		if child_words:
			c.execute("INSERT INTO parent_word (word) VALUES (?)", (word,))
		for i in range(len(child_words)):
			print(child_words[i])
			print(meanings[i])
			c.execute("INSERT INTO child_word (parent_word, child_word, meaning) VALUES (?, ?, ?)", (word, child_words[i], meanings[i]))
	c.close()
	conn.commit()

if __name__ == '__main__':
	words = ['残り', '単語', '節制']
	main(words)
