SED = sed
TAR = tar
GIT = git
PYTHON = python3

PACKAGE = rgwadmin
RELEASE = 1
VERSION = $(shell git describe --abbrev=0 --tags)
OS_MAJOR_VERSION = $(shell grep ^VERSION_ID /etc/os-release | cut -f2 -d \" | cut -f1 -d \.)
OS := rhel$(OS_MAJOR_VERSION)
DIST_DIR := dist/$(OS)
BUILDROOT := /srv/build/$(OS)
RPM_FILE := $(PYTHON)-$(PACKAGE)-$(VERSION)-$(RELEASE).noarch.rpm
YUMREPO_LOCATION=/srv/UMyumrepos/$(OS)/stable

.PHONY: rpm
rpm:
	$(eval TEMPDIR := $(shell mktemp -d /tmp/tmp.XXXXX))
	mkdir -p $(TEMPDIR)/$(PACKAGE)-$(VERSION)
	$(GIT) clone . $(TEMPDIR)/$(PACKAGE)-$(VERSION)
	$(GIT) \
        --git-dir=$(TEMPDIR)/$(PACKAGE)-$(VERSION)/.git \
        --work-tree=$(TEMPDIR)/$(PACKAGE)-$(VERSION) \
        checkout tags/$(VERSION)
	$(TAR) -C $(TEMPDIR) --exclude .git -czf $(BUILDROOT)/SOURCES/$(PACKAGE)-$(VERSION).tar.gz $(PACKAGE)-$(VERSION)
	rpmbuild -bb $(PACKAGE).spec --define "python ${PYTHON}" --define "version ${VERSION}"
	rm -rf $(TEMPDIR)
	mkdir -p $(DIST_DIR)
	cp $(BUILDROOT)/RPMS/noarch/$(RPM_FILE) $(DIST_DIR)

.PHONY: copy_rpm
copy_rpm:
	sudo cp $(DIST_DIR)/$(RPM_FILE) $(YUMREPO_LOCATION)/Packages/noarch

.PHONY: createrepo
createrepo:
	sudo createrepo --workers=4 $(YUMREPO_LOCATION)

.PHONY: tag
tag:
	$(SED) -i 's/__version__ = .*/__version__ = "$(VERSION)"/g' $(PACKAGE)/__init__.py
	$(GIT) add $(PACKAGE)/__init__.py
	$(GIT) commit -m "Tagging $(VERSION)"
	$(GIT) tag -a $(VERSION) -m "Tagging $(VERSION)"

.PHONY: clean
clean:
	rm -rf dist/
