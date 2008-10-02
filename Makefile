#!/usr/bin/make -f
#
# Makefile to assist with publishing the docgen code to admin host

ADMIN_HOST = soldfm

LOGIN_USER = root

SSH_ID = /home/daedalus/.ssh/soldfm-sync

SVN_PATH = svn+ssh://fnordsvn/home/daedalus/svn/docgen/trunk
EXPORT_DIR = docgen-export

VIRT_ROOT = soldfm_root

# Export the latest code to an export location
export: 
	echo "Exporting latest code from repository..."
	-rm -rf $(EXPORT_DIR)
	svn export $(SVN_PATH) $(EXPORT_DIR)

build: build.stamp
	echo "Building DocGen for soldfm install..."
	cd $(EXPORT_DIR); \
	python setup.py install --root $(VIRT_ROOT) --optimize 1 --install-data /usr/local/docgen --install-scripts /usr/local/docgen --install-lib /usr/local/lib/python2.5/site-packages

build.stamp:
	touch build.stamp

build_local: build_local.stamp
	echo "Building DocGen for soldfm install..."
	-rm -rf $(VIRT_ROOT)
	python setup.py install --root $(VIRT_ROOT) --optimize 1 --install-data /usr/local/docgen --install-scripts /usr/local/docgen --install-lib /usr/local/lib/python2.5/site-packages

build_local.stamp:
	touch build_local.stamp

sync:
	echo "Installing latest code to $(ADMIN_HOST)..."
	rsync --dry-run -arv -O --no-p --no-g -e 'ssh -i $(SSH_ID)' $(VIRT_ROOT)/* $(LOGIN_USER)@$(ADMIN_HOST):/
	echo "Done."

sync_local: build_local
	echo "Installing to local host..."
	rsync -arv -O --no-p --no-g $(VIRT_ROOT)/* /

install: export build sync

install_local: build_local sync_local

