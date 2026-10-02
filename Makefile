ROM ?= rom/original.gb
OUTPUT ?= build/translated.gb

.PHONY: self-test test translated audit clean info run debug gui
self-test:
	gb-self-test
test:
	python3 -m unittest discover -s tests -v
translated:
	python3 tools/bin/gb-translate-build $(ROM) -o $(OUTPUT)
audit:
	python3 tools/bin/gb-repo-audit
clean:
	rm -rf build
info:
	gb-rom-info $(ROM)
run:
	gb-run $(OUTPUT)
debug:
	gb-debug $(OUTPUT)
gui:
	start-gb-desktop
