edgar.zip: edgar.py
	mkdir -p build
	cp $< build/
	cp -r venv/lib/python3.5/site-packages/* build/
	zip -r $@ build/*

clean:
	rm -rf build
	rm edgar.zip

.PHONY: clean
