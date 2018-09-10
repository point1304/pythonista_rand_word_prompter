import os, sys, appex, ui, sqlite3, json

import config

class Singleton(type):
	"""Singleton metaclass implementation"""
	_instances = {}
	
	def __call__(cls, *args, **kwargs):
		if cls not in cls._instances:
			cls._instances[cls] = super(Singleton, 
				cls).__call__(*args, **kwargs)
				
		return cls._instances[cls]


class Config(dict, metaclass=Singleton):

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

class MyListDataSourceList (list):
	def __init__(self, seq, datasource):
		list.__init__(self, seq)
		self.datasource = datasource
	
	def append(self, item):
		list.append(self, item)
		self.datasource.reload()
	
	def __setitem__(self, key, value):
		list.__setitem__(self, key, value)
		self.datasource.reload()
	
	def __delitem__(self, key):
		list.__delitem__(self, key)
		self.datasource.reload()
	
	def __setslice__(self, i, j, seq):
		list.__setslice__(self, i, j, seq)
		self.datasource.reload()
	
	def __delslice__(self, i, j):
		list.__delslice__(self, i, j)
		self.datasource.reload()			
			
class MyListDataSource (object):
	def __init__(self, items=None):
		self.tableview = None
		self.reload_disabled = False
		self.delete_enabled = True
		self.move_enabled = False
		
		self.action = None
		self.edit_action = None
		self.accessory_action = None
		
		self.tapped_accessory_row = -1
		self.selected_row = -1
		
		if items is not None:
			self.items = items
		else:
			self.items = MyListDataSourceList([], self)
		self.text_color = None
		self.highlight_color = None
		self.font = None
		self.number_of_lines = 1
	
	def reload(self):
		if self.tableview and not self.reload_disabled:
			self.tableview.reload()
	
	@property
	def items(self):
		return self._items
	
	@items.setter
	def items(self, value):
		self._items = MyListDataSourceList(value, self)
		self.reload()
	
	def tableview_number_of_sections(self, tv):
		self.tableview = tv
		return 1
	
	def tableview_number_of_rows(self, tv, section):
		return len(self.items)
	
	def tableview_can_delete(self, tv, section, row):
		return self.delete_enabled
	
	def tableview_can_move(self, tv, section, row):
		return self.move_enabled
	
	def tableview_accessory_button_tapped(self, tv, section, row):
		self.tapped_accessory_row = row
		if self.accessory_action:
			self.accessory_action(self)
	
	def tableview_did_select(self, tv, section, row):
		self.selected_row = row
		if self.action:
			self.action(self)
	
	def tableview_move_row(self, tv, from_section, from_row, to_section, to_row):
		if from_row == to_row:
			return
		moved_item = self.items[from_row]
		self.reload_disabled = True
		del self.items[from_row]
		self.items[to_row:to_row] = [moved_item]
		self.reload_disabled = False
		if self.edit_action:
			self.edit_action(self)
	
	def tableview_delete(self, tv, section, row):
		self.reload_disabled = True
		del self.items[row]
		self.reload_disabled = False
		tv.delete_rows([row])
		if self.edit_action:
			self.edit_action(self)
	
	def tableview_cell_for_row(self, tv, section, row):
		item = self.items[row]
		cell = ui.TableViewCell()
		cell.text_label.number_of_lines = self.number_of_lines
		cell.name = 'cell_' + str(row)
		if isinstance(item, dict):
			cell.text_label.text = item.get('title', '')
			img = item.get('image', None)
			if img:
				if isinstance(img, basestring):
					cell.image_view.image = Image.named(img)
				elif isinstance(img, Image):
					cell.image_view.image = img
			accessory = item.get('accessory_type', 'none')
			cell.accessory_type = accessory
			"""BEGINNING OF CUSTOM CODE"""	
			child_word = item.get('child_word', None)
			if child_word is not None:
				child_word_lb = ui.Label(frame=(10, 0, 110, 44),
					bounds=(0, 0, 110, 44), name='child_word_lb', flex='hr')
				child_word_lb.alignment = ui.ALIGN_LEFT
				child_word_lb.text = child_word
				child_word_lb.font = ('<system>', 15)
				child_word_lb.text_color = 'blue'
				child_word_lb.number_of_lines = 0
				cell.add_subview(child_word_lb)
				
			meaning = item.get('meaning', None)
			if meaning is not None:
				meaning_lb = ui.Label(frame=(125, 0, 195, 44),
					bounds=(0, 0, 170, 44), name='meaning_lb', flex='whr')
				meaning_lb.text = meaning
				meaning_lb.font = ('<system>', 15)
				meaning_lb.number_of_lines = 0
				cell.add_subview(meaning_lb)
			"""END OF CUSTOM CODE"""
		else:
			cell.text_label.text = str(item)
		if self.text_color:
			cell.text_label.text_color = self.text_color
		if self.highlight_color:
			bg_view = View(background_color=self.highlight_color)
			cell.selected_background_view = bg_view
		if self.font:
			cell.text_label.font = self.font
		return cell

class MainView(ui.View, metaclass=Singleton):
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.config = Config()
		self.current_word = None
		
		self.frame = (0, 36, 359, 500)
		self.bounds = (0, 0, 359, 500)
		self.name = 'main_view'
		self.background_color = (0,0,0,0)
		
		source = get_rand_items()
		self.current_word, ds_items = source[0][0], source[1]
		
		tb_v = ui.TableView(frame=(0, 36, 359, 470),
			bounds=(0, 0, 359, 470), name='tb_v',
			background_color = 'white', flex='wh')
		data_source = MyListDataSource(ds_items)
		tb_v.data_source = data_source
		tb_v.background_color = (0,0,0,0)
		
		shuffle_btn = ui.Button(frame=(359 - 64, 0, 64, 32),
			bounds=(0, 0, 64, 32), name='shuffle_btn',
			title='Shuffle', flex='b', action=self.shuffle_btn_tapped)
		delete_from_db_btn = ui.Button(frame=(356 - 192, 0, 64, 32),
			bounds=(0, 0, 64, 32), name='delete_from_db_btn', title='Delete',
			flex='b', action=self.delete_from_db_btn_tapped)
		endic_fetch_btn = ui.Button(frame=(356 - 128, 0, 64, 32),
			bounds=(0, 0, 64, 32), name='endic_fetch_btn', title='Fetch',
			flex='b', action=self.endic_fetch_btn_tapped)

		components = [
			tb_v, shuffle_btn, delete_from_db_btn,
			endic_fetch_btn,
		]
		for component in components:
			self.add_subview(component)
		
	def shuffle_btn_tapped(self, sender):
		source = get_rand_items()
		self.current_word, data_source = source[0][0], source[1]
		self['tb_v'].data_source.items = data_source
		
	def endic_fetch_btn_tapped(self, sender):
		pass
		
	def delete_from_db_btn_tapped(self, sender):
		db = _get_db()
		cur = db.cursor()
		cur.execute("DELETE FROM parent_word WHERE word = ?",
			(self.current_word,))
		cur.close()
		db.commit()
		db.close()
		self.shuffle_btn_tapped(self['delete_from_db_btn'])
	
	def size_to_fit(self):
		super().size_to_fit()

	def present(self, *args, **kwargs):
		super().present(*args, **kwargs)

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
		db.execute("PRAGMA foreign_keys = ON")
	else:
		db = sqlite3.connect(path,
		detect_types=sqlite3.PARSE_DECLTYPES)
		db.execute("PRAGMA foreign_keys = ON")
	return db
	
def rand_fetch():
	db = _get_db()
	cursor = db.cursor()
	cursor.execute("SELECT word FROM parent_word ORDER BY RANDOM() LIMIT 1")
	try:
		word = cursor.fetchall()[0]
	except IndexError:
		return 'Nothing Found', ['Nothing Found'], [('Nothing Found', 'Please, register words')]
	cursor.execute("SELECT sentence FROM example WHERE word = ?", word)
	sentences = cursor.fetchall()
	cursor.execute("""SELECT child_word, meaning FROM child_word 
		WHERE parent_word = ?""", word)
	child_words_and_meanings = cursor.fetchall()
	cursor.close()
	db.close()
	return word, sentences, child_words_and_meanings

def to_dict(child_word_and_meaning):
	keys = ('child_word', 'meaning')
	return dict(zip(keys ,child_word_and_meaning))

def get_rand_items():
	word, sentences, child_words_and_meanings = rand_fetch()
	data_source = []
	for child_word_and_meaning in child_words_and_meanings:
		data_source.append(to_dict(child_word_and_meaning))
		
	return word, data_source

def main():
	widget_name = __file__ + str(os.stat(__file__).st_mtime)
	mv = appex.get_widget_view()
	if mv is not None and mv.name == widget_name:
		return
	
	mv = MainView()
	appex.set_widget_view(mv)


if __name__ == '__main__':
	main()
