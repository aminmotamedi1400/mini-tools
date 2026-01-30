# Local PDF Retrieval & Analysis Tool

A lightweight, offline-first tool designed for researchers and students to index, search, and retrieve context from large collections of PDF documents.

This tool solves the problem of "multi-document retrieval" by allowing you to index a folder of PDFs (books, papers, reports) and perform context-aware searches. It retrieves exact text snippets, ranks results using BM25/TF-IDF logic, and provides direct page-level navigation.

It is particularly useful for preparing structured context for **AI-assisted analysis** or performing deep literature reviews across multiple sources.

## 🚀 Key Features

- **Multi-PDF Indexing:** One-time indexing of entire folders (incremental updates supported).
- **Context-Aware Retrieval:** Returns the exact text snippet surrounding the search query.
- **Relevance Ranking:** Uses BM25/TF-IDF logic to score results based on term frequency and document length.
- **Smart Navigation:**
  - **SumatraPDF Integration (Recommended):** Opens PDFs at the exact page without opening new windows (Instance Reuse).
  - **Edge Fallback:** Falls back to Microsoft Edge if SumatraPDF is not detected.
- **Research Oriented:** Export results to JSON/Text for further analysis.
- **Offline & Private:** All processing happens locally on your machine.

## 🛠️ Prerequisites

- **OS:** Windows 10/11
- **Python:** 3.8 or higher
- **PDF Viewer:** [SumatraPDF](https://www.sumatrapdfreader.org/free-pdf-reader) (Highly recommended for the best experience with page navigation and highlighting).

## 📦 Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/aminmotamedi1400/mini-tools.git
   cd toolbox/pdf-searcher
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

## 🏃‍♂️ Usage (Running form Source)

To run the application directly with Python:

1. Execute the main UI script:

   ```bash
   python ui.py
   ```

2. **Indexing:**
   - Click **"Browse"** to select your folder containing PDF files.
   - Click **"Build Index"**. (This may take a few moments depending on the number of files).
3. **Searching:**
   - Enter your query (e.g., `multiagent systems` or `"exact phrase"`).
   - Click **Search**.
4. **Navigation:**
   - Click on any result link (e.g., `📄 Open at page 45`) to open the PDF.

## 🏗️ Building the Executable (.exe)

You can convert this tool into a standalone Windows executable using `cx_Freeze`. This allows you to run the tool on computers without Python installed.

1. **Build the application:**

   ```bash
   python setup.py build
   ```

2. **Locate the executable:**
   - Go to the newly created `build/` directory.
   - Look for a folder named starting with `exe.win...`.
   - Run **`PDFSearcher.exe`**.

## ⚙️ Configuration & Viewer Logic

The tool automatically attempts to detect the best available PDF viewer:

1. **SumatraPDF (Priority):** If installed, it uses command-line arguments to:
    - Reuse the existing window (`-reuse-instance`).
    - Jump to the specific page (`-page`).
    - Highlight the search query (`-search`).
2. **Microsoft Edge (Fallback):** Uses standard file protocol (`file://...#page=X`).
3. **System Default:** Opens the file normally if neither is found.

*Tip: For the best workflow, install SumatraPDF and ensure `ReuseInstance = true` is set in SumatraPDF settings.*

## 🤝 Contributing

This project is part of my personal engineering toolbox. Pull requests are welcome for:

- Improved ranking algorithms.
- Better text extraction for multi-column PDFs.
- UI enhancements.

## 📄 License

This project is intended for educational and research purposes.
