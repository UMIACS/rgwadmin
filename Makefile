SED = sed
GIT = git
PACKAGE = rgwadmin

.PHONY: tag
tag:
	$(SED) -i 's/__version__ = .*/__version__ = "$(VERSION)"/g' $(PACKAGE)/__init__.py
	$(GIT) add $(PACKAGE)/__init__.py
	$(GIT) commit -m "Tagging $(VERSION)"
	$(GIT) tag -a $(VERSION) -m "Tagging $(VERSION)"

.PHONY: upload
upload: clean
	python setup.py sdist
	twine upload dist/*


.PHONY: clean
clean:
	rm -rf dist/
