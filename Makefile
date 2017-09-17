build/edgar.zip: edgar.py
	mkdir -p build/edgar
	cp $< build/edgar/
	cp -r samples/ build/edgar/
	cp -r venv/lib/python3.5/site-packages/* build/edgar/
	cd build && zip -r edgar.zip edgar/*

clean:
	rm -rf build
	rm -f edgar.zip

.PHONY: clean
