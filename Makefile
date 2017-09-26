SOURCES:=edgar.py edgar.bat

test: $(SOURCES)
	python3 edgar.py -i example/input.txt -w $(shell mktemp -d) -o $(shell mktemp -d)

build/edgar.zip: $(SOURCES) clean
	mkdir -p build/edgar
	cp $(SOURCES) build/edgar/
	cp -r samples/ build/edgar/
	cp -r venv/lib/python3.5/site-packages/* build/edgar/
	cp README.md build/edgar/
	cd build && zip -r edgar.zip edgar/*
	cp build/edgar.zip ./

release: build/edgar.zip
	semver inc patch
	git commit -am "Releasing $(shell semver tag)"
	git tag -a $(shell semver tag) -m 'Release Tag: $(shell semver tag)'
	@echo "Use git push --tags to push the release to Github."

clean:
	rm -rf build
	rm -f edgar.zip

.PHONY: clean test release
