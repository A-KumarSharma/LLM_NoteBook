# app.py
"""
Mini NotebookLM — vectorless edition.

Instead of embeddings + a vector DB, this indexes page text into a JSON
cache and retrieves relevant pages with simple keyword scoring. That's
enough for small/medium personal notebooks and keeps the whole thing
dependency-light.
"""

import os
import re
import json
import fitz  # PyMuPDF
import ollama
from datetime import datetime

DOC_FOLDER = "documents"
CACHE_FILE = "cache.json"
NOTES_FILE = "notes.txt"

MODEL = "llama3.3"  # <-- verify with `ollama list`; "gemma4:31b-cloud" looked like a typo

MAX_CONTEXT_CHARS = 12000  # rough budget so we don't blow past the model's context window

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "of",
    "to", "in", "on", "for", "and", "or", "what", "which", "who",
    "how", "does", "do", "did", "this", "that", "with", "at", "as",
    "it", "its", "from",
}

os.makedirs(DOC_FOLDER, exist_ok=True)


# ----------------------------
# Cache
# ----------------------------

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print("Warning: cache.json is corrupted, starting fresh.")
                return []
    return []


def save_cache(data):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


pages = load_cache()


def already_indexed(name):
    """Check if a file is already in the cache, so `add` is idempotent."""
    return any(p["file"] == name for p in pages)


# ----------------------------
# Document Loading
# ----------------------------

def add_pdf(path):
    global pages

    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    name = os.path.basename(path)

    if already_indexed(name):
        print(f"{name} is already indexed. Remove it first if you want to re-add it.")
        return

    try:
        doc = fitz.open(path)
    except Exception as e:
        print(f"Could not open PDF: {e}")
        return

    added = 0
    for i, page in enumerate(doc):
        text = page.get_text().strip()
        if text:
            pages.append({
                "file": name,
                "page": i + 1,
                "text": text,
                "preview": text[:300],
            })
            added += 1

    save_cache(pages)
    print(f"Indexed {name}: {added} pages with text (out of {len(doc)} total)")


def add_txt(path):
    global pages

    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    name = os.path.basename(path)

    if already_indexed(name):
        print(f"{name} is already indexed. Remove it first if you want to re-add it.")
        return

    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    pages.append({
        "file": name,
        "page": 1,
        "text": text,
        "preview": text[:300],
    })

    save_cache(pages)
    print(f"Indexed {name}")


def remove_file(name):
    global pages
    before = len(pages)
    pages = [p for p in pages if p["file"] != name]
    save_cache(pages)
    removed = before - len(pages)
    print(f"Removed {removed} page(s) for {name}" if removed else f"No entries found for {name}")


def list_files():
    if not pages:
        print("Notebook is empty.")
        return
    seen = {}
    for p in pages:
        seen[p["file"]] = seen.get(p["file"], 0) + 1
    for name, count in seen.items():
        print(f"{name} — {count} page(s)")


# ----------------------------
# Search (keyword-based, vectorless)
# ----------------------------

def tokenize(query):
    words = re.findall(r"[a-z0-9]+", query.lower())
    return [w for w in words if w not in STOPWORDS] or words  # fall back if everything was a stopword


def search_pages(query, limit=5):
    words = tokenize(query)

    if not words:
        return []

    result = []

    for p in pages:
        text_lower = p["text"].lower()
        score = sum(text_lower.count(w) for w in words)
        if score:
            result.append((score, p))

    result.sort(key=lambda x: x[0], reverse=True)

    return [x[1] for x in result[:limit]]


# ----------------------------
# Ollama
# ----------------------------

def call_model(prompt):
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"]


def ask(question):
    found = search_pages(question)

    if not found:
        return "No matching pages found."

    context = ""
    sources = []

    for p in found:
        chunk = f"\nPAGE {p['page']} FROM {p['file']}\n{p['text']}\n"
        if len(context) + len(chunk) > MAX_CONTEXT_CHARS:
            break
        context += chunk
        sources.append(f"{p['file']} page {p['page']}")

    prompt = f"""You are a notebook assistant.
Answer only using the notebook excerpts below. If the answer isn't in them, say so.

Notebook:
{context}

Question:
{question}

Give a clear, concise answer."""

    answer = call_model(prompt)

    return answer + "\n\nSources:\n" + "\n".join(sources)


# ----------------------------
# Summary
# ----------------------------

def summary():
    if not pages:
        return "Notebook is empty — nothing to summarize."

    text = ""
    for p in pages:
        chunk = p["text"][:1000]
        if len(text) + len(chunk) > MAX_CONTEXT_CHARS:
            break
        text += chunk + "\n\n"

    prompt = f"""Summarize the following notebook contents in a clear, organized way.
Use short sections or bullet points if there are multiple distinct topics.

Notebook contents:
{text}"""

    return call_model(prompt)


# ----------------------------
# Notes
# ----------------------------

def show_notes():
    if os.path.exists(NOTES_FILE):
        print(open(NOTES_FILE, encoding="utf-8").read())
    else:
        print("No notes")


def add_note(text):
    with open(NOTES_FILE, "a", encoding="utf-8") as f:
        f.write("\n" + datetime.now().strftime("%Y-%m-%d") + " " + text)
    print("Saved")


# ----------------------------
# CLI
# ----------------------------

HELP = """
Mini NotebookLM (vectorless)

Commands:

add <file>        index a .pdf or .txt file (looked up as-is, or in documents/)
list              show indexed files
remove <file>      remove a file from the notebook
ask <question>     ask a question, answered from the notebook + sources
summary            summarize the whole notebook
search <words>      raw keyword search, no LLM call
notes              show saved notes
note <text>         save a note
exit
"""


def resolve_path(file):
    """Allow bare filenames to resolve inside DOC_FOLDER too."""
    if os.path.exists(file):
        return file
    candidate = os.path.join(DOC_FOLDER, file)
    if os.path.exists(candidate):
        return candidate
    return file  # let the caller report "not found"


def main():
    print(HELP)

    while True:
        cmd = input("> ").strip()

        if cmd == "exit":
            break

        elif cmd.startswith("add "):
            file = resolve_path(cmd[4:].strip())
            if file.endswith(".pdf"):
                add_pdf(file)
            elif file.endswith(".txt"):
                add_txt(file)
            else:
                print("Unsupported file type (use .pdf or .txt)")

        elif cmd == "list":
            list_files()

        elif cmd.startswith("remove "):
            remove_file(cmd[7:].strip())

        elif cmd.startswith("ask "):
            print(ask(cmd[4:]))

        elif cmd == "summary":
            print(summary())

        elif cmd.startswith("search "):
            results = search_pages(cmd[7:])
            if not results:
                print("No matches.")
            for r in results:
                print(r["file"], "page", r["page"], "-", r["preview"][:80])

        elif cmd == "notes":
            show_notes()

        elif cmd.startswith("note "):
            add_note(cmd[5:])

        elif cmd == "help":
            print(HELP)

        else:
            print("Unknown command (type 'help')")


if __name__ == "__main__":
    main()
