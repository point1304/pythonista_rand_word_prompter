import os, appex, sqlite3

from ui import (ListDataSourceList, View, Label,
	TableViewCell, TableView, SegmentedControl, Button, ALIGN_LEFT)

from config import appconfig
from json import dumps as json_dumps, loads as json_loads

# TODO: Remove redundant items; e.g. accessory actions.
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
			self.items = ListDataSourceList([], self)
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
		self._items = ListDataSourceList(value, self)
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
		cell = TableViewCell()
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
				child_word_lb = Label(frame=(10, 0, 110, 44),
					bounds=(0, 0, 110, 44), name='child_word_lb', flex='hr')
				child_word_lb.alignment = ALIGN_LEFT
				child_word_lb.text = child_word
				child_word_lb.font = ('<system>', 15)
				child_word_lb.text_color = appconfig['FONT_COLOR']
				child_word_lb.number_of_lines = 0
				cell.add_subview(child_word_lb)
				
			meaning = item.get('meaning', None)
			if meaning is not None:
				meaning_lb = Label(frame=(125, 0, 195, 44),
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

class MainView(View):
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._current_word = None
		self._lang_code = 1
		
		self.frame = (0, 36, 359, 467)
		self.bounds = (0, 0, 359, 467)
		self.name = 'main_view'
		self.background_color = (0,0,0,0)
		
		source = self.get_rand_items()
		self._current_word, ds_items = source[0][0], source[1]
		
		tb_v = TableView(frame=(0, 36, 359, 431), bounds=(0, 0, 359, 431),
			name='tb_v', background_color =(0, 0, 0, 0), flex='wh',
			row_height=36, data_source=MyListDataSource(ds_items))
		
		#: FYI: iphone widget width = 356		
		shuffle_btn = Button(frame=(289 + 15, 4, 64, 32),
			bounds=(0, 0, 64, 32), name='shuffle_btn',
			title='Shuffle', flex='lb', action=self.shuffle_btn_tapped,
			border_width=appconfig['BORDER_WIDTH'],
			corner_radius=appconfig['CORNER_RADIUS'])
		delete_from_db_btn = Button(frame=(145 + 19, 4, 64, 26),
			bounds=(0, 0, 64, 26), name='delete_from_db_btn', title='Delete',
			flex='lb', action=self.delete_from_db_btn_tapped,
			border_width=appconfig['BORDER_WIDTH'],
			corner_radius=appconfig['CORNER_RADIUS'])
		lang_ctrl = SegmentedControl(frame=(217, 4, 64, 26),
			bounds=(0, 0, 70, 26), name='lang_ctrl', flex='lb',
			segments=('EN', 'JP'), action=self.lang_ctrl_tapped)
		word_lb = Label(frame=(5, 1, 136, 32), bounds=(0, 0, 136, 32),
			name='word_lb', flex='b', text=self._current_word,
			font=('<system-bold>', 18))
		
		btns = {shuffle_btn, delete_from_db_btn}
		for btn in btns:
			btn.flex = 'lb'
			btn.border_width = appconfig['BORDER_WIDTH']
			btn.corner_radius = appconfig['CORNER_RADIUS']
			btn.border_color = appconfig['BORDER_COLOR']
			
		components = {tb_v, lang_ctrl, word_lb}
		components.update(btns)
		for component in components:
			self.add_subview(component)
		
		lang_ctrl.selected_index = self._lang_code
	
	def lang_ctrl_tapped(self, sender):
		# EN seg tapped				
		if sender.selected_index == 0:
			if self._lang_code == 1:
				self._lang_code = 0
				self.shuffle_btn_tapped(sender)
		# JP seg tapped
		elif sender.selected_index == 1:
			if self._lang_code == 0:
				self._lang_code = 1
				self.shuffle_btn_tapped(sender)
			
	def shuffle_btn_tapped(self, sender):
		c = 2
		while True:
			source = self.get_rand_items()
			new_word = source[0][0]
			if new_word != self._current_word:
				break
			elif '<' and '>' in new_word:
				break
			elif not c:
				break
			#TODO: Counter is a temp implementation. Must be fixed into an algorithm
			# which catches the word-count of the :db: worddb and break the loop if the count equals to 0.
			c -= 1
		
		data_source = source[1]
		self._current_word = new_word
		self['word_lb'].text = self._current_word
		self['tb_v'].data_source.items = data_source
		res = {
			'wd_now' : self._current_word,
			'lang' : self._lang_code,
		}
		res = json_dumps(res)
		with open(appconfig['LAST_RESULT_PATH'], 'w') as f:
			f.write(res)
		
	def delete_from_db_btn_tapped(self, sender):
		db = _get_db()
		cur = db.cursor()
		if self._lang_code == 0:
			cur.execute("DELETE FROM parent_word WHERE word = ?",
				(self._current_word,))
		elif self._lang_code == 1:
			cur.execute("DELETE FROM jp_parent_word WHERE jp_word = ?",
				(self._current_word,))
		cur.close()
		db.commit()
		db.close()
		self.shuffle_btn_tapped(sender)

	def get_rand_items(self):
		def _to_ds_format(child_word_and_meaning):
			keys = ('child_word', 'meaning')
			return dict(zip(keys ,child_word_and_meaning))

		word, sentences, child_words_and_meanings = self._rand_fetch()
		data_source = []
		for child_word_and_meaning in child_words_and_meanings:
			data_source.append(_to_ds_format(child_word_and_meaning))
		return word, data_source

	def _rand_fetch(self):
		db = _get_db()
		cursor = db.cursor()
		# If en mode
		if self._lang_code == 0:
			cursor.execute("SELECT word FROM parent_word ORDER BY RANDOM() LIMIT 1")
			try:
				word = cursor.fetchall()[0]
			except IndexError:
				return (('<No Words>',), ['Nothing Found'], 
					[('Nothing Found', 'Please, register words')])
			cursor.execute("SELECT sentence FROM example WHERE word = ?", word)
			sentences = cursor.fetchall()
			cursor.execute("""SELECT child_word, meaning FROM child_word 
				WHERE parent_word = ?""", word)
			child_words_and_meanings = cursor.fetchall()
	
		# If jp mode
		elif self._lang_code == 1:
			cursor.execute("SELECT jp_word FROM jp_parent_word ORDER BY RANDOM() LIMIT 1")
			try:
				word = cursor.fetchall()[0]
			except IndexError:
				return (('<単語登録無し>',), ['例えがありません'], 
					[('単語登録無し','単語を登録してください')])
			cursor.execute("SELECT jp_sentence FROM jp_example WHERE jp_word = ?", word)
			sentences = cursor.fetchall()
			cursor.execute("""SELECT jp_child_word, jp_meaning FROM jp_child_word
				WHERE jp_parent_word = ?""", word)
			child_words_and_meanings = cursor.fetchall()
		
		cursor.close()
		db.close()
		return word, sentences, child_words_and_meanings

def _get_db():
	path = appconfig['DATABASE']
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


def main():
	widget_name = __file__ + str(os.stat(__file__).st_mtime)
	mv = appex.get_widget_view()
	if mv is not None and mv.name == widget_name:
		return
	
	mv = MainView()
	
	#: Button sizing; if a :param: `title` or `image` is passed to the
	#: ui.Button's constructor, it automatically determines its size
	#: ignoring the width and length elements of the :param: `frame` and `bounds`.
	#: This is not a bug but an intended feature and requires a user to re-configure
	#: :inst: ui.Buttons in a way that s/he wants them to be.
	btns = [mv['shuffle_btn'], mv['delete_from_db_btn'],]
	btn_width = appconfig['BTN_WIDTH']
	for btn in btns:
		f_now = btn.frame
		btn.frame = (f_now[0] - (btn_width - f_now[2]), f_now[1], f_now[2], f_now[3])
		btn.width = btn_width
		btn.height = 26
	print(mv.frame, mv.bounds)
	print(mv['tb_v'].frame)
	appex.set_widget_view(mv)

if __name__ == '__main__':
	main()
