ROOT := $(shell pwd)
PREFIX := $(shell readlink -f ~/.local)
OBJECTS := config.ini gui-appindicator.py gui-systray.py update.py

uninstall:
	rm -r $(PREFIX)/share/lightndark
	rm $(PREFIX)/bin/lightndark-gui
	rm $(PREFIX)/share/icons/lightndark.svg
	rm $(PREFIX)/share/applications/lightndark.desktop

install:
	mkdir -p $(PREFIX)/share/icons
	mkdir -p $(PREFIX)/share/applications
	mkdir -p $(PREFIX)/share/lightndark/thirdparty
	mkdir -p $(PREFIX)/bin
	cp -a $(OBJECTS) $(PREFIX)/share/lightndark/
	cp -a thirdparty/bbr_color.txt $(PREFIX)/share/lightndark/thirdparty/
	cp -a lightndark-gui $(PREFIX)/bin/
	cp -a lightndark.svg $(PREFIX)/share/icons/
	cp -a lightndark.desktop $(PREFIX)/share/applications/

all:
	@echo "Usage: $0 [install|uninstall]"

