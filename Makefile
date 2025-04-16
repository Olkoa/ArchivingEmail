# Okloa Project Makefile
# Simple commands for setting up and running the project

# Default Python interpreter
PYTHON = python
# Streamlit command
STREAMLIT = streamlit

# Project directories
APP_DIR = app
DATA_DIR = data

# MCP command (Model Context Protocol server)
MCP_PATH = /mnt/c/Users/julie/Projects
MCP_COMMAND = npx -y @modelcontextprotocol/server-filesystem

# Help command - displays available commands
.PHONY: help
help:
	@echo "Okloa Project Commands:"
	@echo "  make setup         - Install dependencies"
	@echo "  make data          - Generate sample data"
	@echo "  make run           - Run Streamlit app (stable mode)"
	@echo "  make run-debug     - Run Streamlit app with debug options"
	@echo "  make run-normal    - Run Streamlit app with normal watcher"
	@echo "  make clean         - Clean generated data"
	@echo "  make start_mcp     - Start the MCP server for Claude Desktop"
	@echo "  make all           - Setup, generate data, and run app"

# Install dependencies
.PHONY: setup
setup:
	$(PYTHON) -m pip install -r requirements.txt

# Generate sample data
.PHONY: data
data:
	$(PYTHON) generate_samples.py

# Run the app in stable mode (no file watcher)
.PHONY: run
run:
	cd $(APP_DIR) && $(STREAMLIT) run app.py --server.fileWatcherType none

# Run the app with debug flag
.PHONY: run-debug
run-debug:
	cd $(APP_DIR) && $(STREAMLIT) run app.py --debug

# Run the app with normal file watcher
.PHONY: run-normal
run-normal:
	cd $(APP_DIR) && $(STREAMLIT) run app.py

# Start the MCP server
.PHONY: start_mcp
start_mcp:
	$(MCP_COMMAND) $(MCP_PATH)

# Clean generated data
.PHONY: clean
clean:
	rm -rf $(DATA_DIR)/raw/mailbox_*
	rm -rf $(DATA_DIR)/processed/*

# Setup, generate data, and run app
.PHONY: all
all: setup data run

# Default target
.DEFAULT_GOAL := help

# Transform .pst files in raw in eml in processed
.PHONY: pst_transform
pst_transform:
	readpst -j 0 -e -o data/processed/celine_readpst_with_S data/raw/celine.guyon.pst



# Transform .pst files in raw in eml in processed
.PHONY: ask_chatbot
ask_chatbot:
	python ${MCP_PATH}/olkoa/src/features/chatbot.py
