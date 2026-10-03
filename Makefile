PROJECT ?= gb-db-z-gokou
ROM ?= roms/$(PROJECT)/original.gb
OUTPUT ?= build/$(PROJECT)/translated.gb

.PHONY: self-test projects validate test test-toolkit test-project translated audit clean info run debug gui

self-test:
	tools/bin/gb-self-test

projects:
	python3 tools/bin/gb-workstation list

validate:
	python3 tools/bin/gb-workstation validate $(PROJECT)

test: test-toolkit test-project

test-toolkit:
	PYTHONPATH=toolkit python3 -m unittest discover -s tests/toolkit -v

test-project:
	python3 tools/bin/gb-workstation test $(PROJECT)

translated:
	python3 tools/bin/gb-workstation build $(PROJECT) --rom $(ROM) --output $(OUTPUT)

audit:
	python3 tools/bin/gb-repo-audit

clean:
	rm -rf build

info:
	python3 tools/bin/gb-workstation info $(PROJECT)

run:
	gb-run $(OUTPUT)

debug:
	gb-debug $(OUTPUT)

gui:
	start-gb-desktop
