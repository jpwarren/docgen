#!/usr/bin/make -f
# $Id$

LOGIN_USER = root

SSH_ID = /home/daedalus/.ssh/soldfm-sync

SVN_PATH = svn+ssh://fnordsvn/home/daedalus/svn/docgen/trunk
EXPORT_DIR = docgen-export

DOCGEN_ROOT = /usr/local/docgen

VIRT_ROOT = docgen_root

RSYNC_FLAGS = -arv -O --no-p --no-g

VERSION := $(shell python setup.py --fullname)

# Some permissions settings required for Sensis
SENSIS_ROOT := 0
SENSIS_USER := 6668
SENSIS_GROUP := 300

build: build.stamp export
	echo "Building DocGen for binary installation..."
	cd $(EXPORT_DIR); \
	python setup.py install --root $(VIRT_ROOT) --optimize 1 --install-data $(DOCGEN_ROOT) --install-scripts $(DOCGEN_ROOT) --install-lib /usr/local/lib/python2.5/site-packages

# Export the latest code to an export location
export: 
	echo "Exporting latest code from repository..."
	-rm -rf $(EXPORT_DIR)
	svn export $(SVN_PATH) $(EXPORT_DIR)

sdist: export
	echo "Creating source distribution for install."
	cd $(EXPORT_DIR); \
	python setup.py sdist

build.stamp:
	touch build.stamp

# Custom build for binary distribution to Sensis
build_sensis: build_sensis.stamp
	echo "Building DocGen for Sensis..."
	cd $(EXPORT_DIR); \
	python setup.py install --root $(VIRT_ROOT) --optimize 1 --install-data $(DOCGEN_ROOT) --install-scripts $(DOCGEN_ROOT) --install-lib /usr/local/lib/python2.5/site-packages

build_sensis.stamp:
	touch build_sensis.stamp

chown_sensis:
	cd $(EXPORT_DIR)/$(VIRT_ROOT); \
	chown -R $(SENSIS_ROOT):$(SENSIS_ROOT) usr/local/lib/python2.5/site-packages/docgen; \
	chown -R $(SENSIS_ROOT):$(SENSIS_ROOT) usr/local/lib/python2.5/site-packages/DocGen*

	cd $(EXPORT_DIR)/$(VIRT_ROOT); \
	chown -R $(SENSIS_ROOT):$(SENSIS_GROUP) $(DOCGEN_ROOT)

sync_local: build
	echo "Installing to local host..."
	cd $(EXPORT_DIR)/$(VIRT_ROOT);\
	rsync $(RSYNC_FLAGS) * /

install: export build

install_local: build sync_local

sensis: export build_sensis
	-mkdir dist
	cd $(EXPORT_DIR)/$(VIRT_ROOT); \
	tar cvzf "$(VERSION).sensis.tar.gz" *
	mv $(EXPORT_DIR)/$(VIRT_ROOT)/$(VERSION).sensis.tar.gz dist/
	echo "Build of Sensis DocGen distro complete: dist/$(VERSION).sensis.tar.gz"
