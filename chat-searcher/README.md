# ChatRecall 🧠

**Turn your AI chat logs into a searchable Knowledge Base integrated with Obsidian.**

`ChatRecall` is a lightweight, local-first tool designed to index, search, and retrieve specific information from your archived AI conversations (ChatGPT, Claude, etc.) saved as Markdown files. It bridges the gap between your chat history and your **Obsidian Vault**.

## 🚀 Why use ChatRecall?

If you save your AI chats as Markdown files, you know that finding *that one specific code snippet* or *explanation* from months ago is difficult. Standard file search only gives you filenames.

**ChatRecall changes that:**

- **Search deeply:** Finds keywords inside specific messages.
- **Context aware:** Shows you *who* said it (User vs. Assistant) and the surrounding text.
- **Obsidian Native:** Opens the search result directly in **Obsidian**, allowing you to link, refactor, and connect ideas immediately.

## ✨ Key Features

- **📂 Bulk Indexing:** Scans folders recursively for `.md` chat logs.
- **⚡ Fast Search:** Uses a local inverted index for instant results.
- **🔗 Obsidian Integration:**

  - Auto-detects if your chats are inside an Obsidian Vault.
  - Opens files using the `obsidian://` protocol.
  - Supports global Vault search triggering.
- **📝 Smart Parsing:** Understands chat structures (Dates, Roles, Titles).
- **🔒 Private & Offline:** No data leaves your computer. Everything runs locally.

## 🛠️ Prerequisites

- **OS:** Windows 10/11 (for the .exe version) or any OS with Python.
- **Obsidian:** Installed and configured (for the integration features).
- **Chat Format:** Supports Markdown files with standard header structures (e.g., `**Date:**`, `## User`, `## Assistant`).

## 📦 Installation

### Option A: Run from Source

1. **Clone the repo:**

   ```bash
   git clone https://github.com/aminmotamedi1400/mini-tools.git
   cd mini-tools/chat-searcher
   ```
  
2. **Install dependencies:**
   *(Note: This tool uses standard Python libraries. Only `cx_Freeze` is needed if you want to build the executable).*

   ```bash
   pip install cx_Freeze
   ```

3. **Run the app:**

   ```bash
   python chat_ui.py
   ```

### Option B: Build Executable (.exe)

To create a standalone portable file for Windows:

```bash
python setup.py build
```

The executable will be located in the `build/` directory.

## 📖 Usage Guide

1. **Launch ChatRecall.**
2. **Select Folder:** Click "Browse" and select the folder where your Markdown chat logs are stored.
   - *Tip: For best results, select a folder inside your Obsidian Vault.*
3. **Build Index:** Click "Build Index". The tool will scan and parse your chats.
4. **Search:**
   - Type your query (e.g., `python decoraters` or `neural network definition`).
   - Press Enter.
5. **Navigate:**
   - Click **"📝 Open in Obsidian"** on any result to jump to that note in your vault.
   - Click **"🔍 Search in Obsidian"** to perform a deep vault search for the same query.

## ⚙️ How Obsidian Detection Works

The tool looks for a `.obsidian` configuration folder in the parent directories of your selected chat folder.

- **If found:** It treats the folder as a Vault and generates `obsidian://` links.
- **If not found:** It falls back to opening the file with your default system text editor (e.g., VS Code, Notepad).

## 🤝 Contributing

This tool is part of a personal productivity toolbox. Pull requests are welcome!

- **Roadmap:**

  - Support for JSON export formats.
  - Semantic search using local embeddings.
  - Dark mode UI.

## 📄 License

This project is open-source and available for educational and research purposes.
