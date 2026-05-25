IPSW ?=
HEADERS_DIR ?= headers
PORT ?= 8080

.PHONY: help dump site serve clean

help:
	@echo "iOS Header Dump"
	@echo ""
	@echo "Usage:"
	@echo "  make dump  IPSW=~/Downloads/iPhone18,3_26.5_23F77_Restore.ipsw"
	@echo "  make site"
	@echo "  make serve"
	@echo ""
	@echo "Variables:"
	@echo "  IPSW         Path to .ipsw file (required for dump)"
	@echo "  HEADERS_DIR  Output directory (default: headers)"
	@echo "  PORT         HTTP server port (default: 8080)"

all: dump site

dump:
	@if [ -z "$(IPSW)" ]; then echo "Error: IPSW variable required. Example: make dump IPSW=~/Downloads/firmware.ipsw"; exit 1; fi
	bash scripts/dump.sh "$(IPSW)" "$(HEADERS_DIR)"

site:
	python3 scripts/generate_site.py "$(HEADERS_DIR)"

serve:
	@echo "Serving http://localhost:$(PORT)/index.html"
	cd "$(HEADERS_DIR)" && python3 -m http.server $(PORT)

clean:
	@echo "This will delete all dumped headers. Are you sure? (ctrl+c to cancel)"
	@read _confirm
	rm -rf $(HEADERS_DIR)
