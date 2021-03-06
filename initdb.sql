DROP TABLE IF EXISTS parent_word;
DROP TABLE IF EXISTS child_word;
DROP TABLE IF EXISTS example;
DROP TABLE IF EXISTS jp_parent_word;
DROP TABLE IF EXISTS jp_child_word;
DROP TABLE IF EXISTS jp_example;

CREATE TABLE parent_word (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	word TEXT UNIQUE NOT NULL
);

CREATE TABLE jp_parent_word (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	jp_word TEXT UNIQUE NOT NULL
);

CREATE TABLE child_word (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	parent_word TEXT NOT NULL,
	child_word TEXT NOT NULL,
	meaning TEXT NOT NULL,
	FOREIGN KEY (parent_word) REFERENCES parent_word (word)
	ON DELETE CASCADE
);

CREATE TABLE jp_child_word (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	jp_parent_word TEXT NOT NULL,
	jp_child_word TEXT NOT NULL,
	jp_meaning TEXT NOT NULL,
	FOREIGN KEY (jp_parent_word) REFERENCES jp_parent_word (jp_word)
	ON DELETE CASCADE
);

CREATE TABLE example (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	word TEXT NOT NULL,
	sentence TEXT NOT NULL,
	FOREIGN KEY (word) REFERENCES parent_word (word)
	ON DELETE CASCADE
);

CREATE TABLE jp_example (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	jp_word TEXT NOT NULL,
	jp_sentence TEXT NOT NULL,
	FOREIGN KEY (jp_word) REFERENCES jp_parent_word (jp_word)
	ON DELETE CASCADE
);
