# Top-level Makefile
# Delegates targets to Makefile.docs

include Makefile.docs

.PHONY: help 
help: _list-targets ## Prints all availble targets

.PHONY: _list-targets
_list-targets: ## This collects and prints all targets, ignore internal commands
	@echo "Available targets:"
	@awk -F'[:#]' '                                               \
		/^[a-zA-Z0-9._-]+:([^=]|$$)/ {                            \
			target = $$1;                                         \
			comment = "";                                         \
			if (match($$0, /## .*/))                              \
				comment = substr($$0, RSTART + 3);                \
			if (target != ".PHONY" && target !~ /^_/ && !seen[target]++) \
				printf "  make %-20s # %s\n", target, comment;    \
		}' $(MAKEFILE_LIST) | sort