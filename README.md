# 📚 Mini NotebookLM (Vectorless Edition)

A lightweight, local NotebookLM-style application built with **Python**, **Ollama**, and **PyMuPDF**.

Instead of using embeddings or a vector database, this project performs **keyword-based page retrieval** and uses a local LLM through Ollama to answer questions from your documents.

Perfect for personal notebooks, PDFs, research papers, and documentation without requiring heavy dependencies or cloud APIs.

---

## Features

- 📄 Index PDF and text files
- 🔍 Fast keyword-based search (no vector database)
- 🤖 Ask questions using a local Ollama model
- 📝 Keep personal notes
- 📚 Summarize all indexed documents
- 🗑 Remove indexed documents
- 💾 Persistent JSON cache
- 🔒 Runs completely offline

---

## How It Works

1. Documents are loaded from PDFs or text files.
2. Each PDF page is stored separately in `cache.json`.
3. User questions are tokenized into keywords.
4. Matching pages are ranked using simple keyword frequency.
5. The most relevant pages are sent to the local LLM.
6. The model answers using only the retrieved context and includes page references.

No embeddings.
No vector databases.
No external APIs.

---

## Project Structure

```
.
├── app.py
├── cache.json
├── documents/
├── notes.txt
└── README.md
```

---

## Requirements

- Python 3.10+
- Ollama installed
- A supported Ollama model (default: `llama3.3`)

Install dependencies:

```bash
pip install pymupdf ollama
```

---

## Install Ollama

Download Ollama:

https://ollama.com

Pull a model:

```bash
ollama pull llama3.3
```

You can use any compatible model by changing:

```python
MODEL = "llama3.3"
```

---

## Running the Project

```bash
python app.py
```

You'll see:

```
Mini NotebookLM (vectorless)

Commands:

add <file>
list
remove <file>
ask <question>
summary
search <words>
notes
note <text>
exit
```

---

# Usage

## Add a PDF

```text
> add research.pdf
```

or place it inside the `documents` folder:

```text
documents/
    research.pdf
```

Then:

```text
> add research.pdf
```

---

## Add a Text File

```text
> add notes.txt
```

---

## List Documents

```text
> list
```

Example:

```
research.pdf — 18 page(s)
notes.txt — 1 page(s)
```

---

## Search Documents

Keyword search without using the language model.

```text
> search transformer attention
```

Example:

```
research.pdf page 8 - Attention is computed...
research.pdf page 9 - Multi-head attention...
```

---

## Ask Questions

```text
> ask What is multi-head attention?
```

Example output:

```
Multi-head attention allows the model to attend to
multiple representation subspaces simultaneously...

Sources:
research.pdf page 8
research.pdf page 9
```

---

## Summarize Notebook

```text
> summary
```

The model summarizes all indexed documents into an organized overview.

---

## Notes

Save a note:

```text
> note Read chapter 5 tomorrow
```

View notes:

```text
> notes
```

---

## Remove a Document

```text
> remove research.pdf
```

The cached pages for that document are deleted.

---

# Cache

Indexed pages are stored in:

```
cache.json
```

Each page contains:

```json
{
  "file": "research.pdf",
  "page": 12,
  "text": "...",
  "preview": "..."
}
```

This avoids reprocessing documents every time the application starts.

---

# Retrieval Strategy

Unlike traditional Retrieval-Augmented Generation (RAG), this project does **not** use:

- FAISS
- ChromaDB
- Pinecone
- Weaviate
- embeddings

Instead it:

- tokenizes the query
- removes stop words
- counts keyword occurrences on every page
- ranks pages by frequency
- sends the best pages to the LLM

This makes the project:

- lightweight
- easy to understand
- dependency-light
- suitable for small and medium personal document collections

---

# Configuration

Adjust these settings in `app.py`:

```python
MODEL = "llama3.3"

MAX_CONTEXT_CHARS = 12000

DOC_FOLDER = "documents"
```

---

# Supported File Types

- PDF (`.pdf`)
- Plain text (`.txt`)

---

# Limitations

- Keyword matching only (no semantic search)
- Large notebooks may miss relevant pages if keywords differ
- OCR is not performed on scanned PDFs
- Context size is limited by the selected Ollama model

---

# Future Improvements

- BM25 ranking
- OCR support for scanned PDFs
- Markdown support
- DOCX support
- Incremental indexing
- Better relevance scoring
- Metadata filters
- Highlight matching passages
- Optional embedding-based retrieval
- Web interface (Streamlit or Gradio)

---

# Example Session

```text
> add ai_book.pdf

Indexed ai_book.pdf: 312 pages

> ask What is reinforcement learning?

Reinforcement learning is a machine learning paradigm
where an agent learns through interaction with an environment
to maximize cumulative reward.

Sources:
ai_book.pdf page 210
ai_book.pdf page 211

> summary

The notebook covers:

• Machine Learning
• Neural Networks
• Transformers
• Reinforcement Learning
• Computer Vision

> note Revise Chapter 8

Saved

> exit
```

---

# License

This project is open source and available under the MIT License.

---

# Acknowledgements

- **Ollama** for local LLM inference
- **PyMuPDF** for fast PDF text extraction
- Python community for the excellent ecosystem

---

## Author

Built as a lightweight, offline NotebookLM-inspired document assistant using Python and Ollama.
