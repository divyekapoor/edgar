build/edgar.zip: edgar.py clean
	mkdir -p build/edgar
	cp $< build/edgar/
	cp -r samples/ build/edgar/
	cp -r venv/lib/python3.5/site-packages/* build/edgar/
	cp README.md build/edgar/
	cd build && zip -r edgar.zip edgar/*
	cp build/edgar.zip ./

release: build/edgar.zip
	semver inc patch
	git commit -am "Releasing $(shell semver tag)"
	git tag -a $(shell semver tag)

clean:
	rm -rf build
	rm -f edgar.zip

.PHONY: clean
