# Top-level Makefile
# Delegates targets to Makefile.docs

include Makefile.docs

.PHONY: help
help:
	@echo "Top-level targets:"
	@echo "  make help           - Run Help command"
	@echo
	@echo "Documentation-specific targets from Makefile.docs:"
	@$(MAKE) -s -f Makefile.docs list-docs-targets
