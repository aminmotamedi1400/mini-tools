# indexer.py
import os
import json
import re
import math
import hashlib
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import PyPDF2


class PDFIndexer:
    STOPWORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
        'this', 'that', 'these', 'those', 'it', 'its', 'they', 'them', 'their',
        'we', 'us', 'our', 'you', 'your', 'he', 'him', 'his', 'she', 'her',
        'which', 'who', 'whom', 'what', 'where', 'when', 'why', 'how',
        'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other',
        'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
        'than', 'too', 'very', 'just', 'also', 'now', 'here', 'there', 'then'
    }
    
    # BM25 parameters
    K1 = 1.5
    B = 0.75
    
    def __init__(self, pdf_directory, index_file="pdf_index.json"):
        self.pdf_directory = Path(pdf_directory)
        self.index_file = Path(pdf_directory) / ".index" / index_file
        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        self.index = None
        self.total_pages = 0
        self.avg_doc_len = 0
    
    def _get_file_hash(self, file_path):
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            buf = f.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()
    
    def extract_text_from_pdf(self, pdf_path):
        try:
            text_content = []
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    raw_text = page.extract_text() or ""
                    cleaned_text = self._clean_text(raw_text)
                    text_content.append({
                        "page_number": page_num,
                        "content": cleaned_text,
                        "content_lower": cleaned_text.lower()
                    })
            return text_content, len(text_content)
        except Exception as e:
            print(f"✗ Error reading {pdf_path.name}: {e}")
            return None, 0
    
    def _clean_text(self, text):
        """Clean text while preserving readability"""
        # Remove multiple spaces but keep single spaces
        text = re.sub(r'[ \t]+', ' ', text)
        # Remove multiple newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        # Remove weird characters but keep punctuation
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\'\"\n]', '', text)
        return text.strip()
    
    def tokenize(self, text, remove_stopwords=True):
        words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
        if remove_stopwords:
            words = [w for w in words if w not in self.STOPWORDS]
        return words
    
    def _calculate_idf(self, word):
        """Calculate IDF for BM25"""
        doc_freq = len(self.index["word_index"].get(word, []))
        if doc_freq == 0:
            return 0
        return math.log((self.total_pages - doc_freq + 0.5) / (doc_freq + 0.5) + 1)
    
    def _calculate_bm25_score(self, word, tf, doc_len):
        """Calculate BM25 score for a word in a document"""
        idf = self._calculate_idf(word)
        numerator = tf * (self.K1 + 1)
        denominator = tf + self.K1 * (1 - self.B + self.B * (doc_len / self.avg_doc_len))
        return idf * (numerator / denominator)
    
    def build_index(self, incremental=True):
        pdf_files = list(self.pdf_directory.glob("**/*.pdf"))
        
        if incremental and self.index_file.exists():
            self.load_index()
            existing_hashes = self.index.get("file_hashes", {})
        else:
            existing_hashes = {}
            self.index = {
                "documents": {},
                "word_index": defaultdict(list),
                "file_hashes": {},
                "metadata": {
                    "last_updated": None,
                    "total_documents": 0,
                    "total_pages": 0,
                    "avg_doc_len": 0
                }
            }
        
        total_pages = 0
        total_words = 0
        new_files = 0
        
        for idx, pdf_path in enumerate(pdf_files, 1):
            file_hash = self._get_file_hash(pdf_path)
            doc_id = str(pdf_path.relative_to(self.pdf_directory))
            
            if doc_id in existing_hashes and existing_hashes[doc_id] == file_hash:
                print(f"Skipping ({idx}/{len(pdf_files)}): {pdf_path.name} (unchanged)")
                # Count existing pages
                if doc_id in self.index["documents"]:
                    for page in self.index["documents"][doc_id]["pages"]:
                        total_pages += 1
                        total_words += page.get("word_count", 0)
                continue
            
            print(f"Processing ({idx}/{len(pdf_files)}): {pdf_path.name}")
            
            text_content, num_pages = self.extract_text_from_pdf(pdf_path)
            
            if not text_content:
                continue
            
            # Remove old entries if updating
            if doc_id in self.index["documents"]:
                self._remove_doc_from_word_index(doc_id)
            
            self.index["documents"][doc_id] = {
                "filename": pdf_path.name,
                "path": str(pdf_path.absolute()),
                "num_pages": num_pages,
                "pages": []
            }
            self.index["file_hashes"][doc_id] = file_hash
            
            for page_data in text_content:
                words = self.tokenize(page_data["content"])
                word_freq = defaultdict(int)
                for w in words:
                    word_freq[w] += 1
                
                self.index["documents"][doc_id]["pages"].append({
                    "page_number": page_data["page_number"],
                    "content": page_data["content"],
                    "content_lower": page_data["content_lower"],
                    "word_count": len(words),
                    "word_freq": dict(word_freq)
                })
                
                for word in set(words):
                    self.index["word_index"][word].append({
                        "doc_id": doc_id,
                        "page": page_data["page_number"],
                        "freq": word_freq[word]
                    })
                
                total_pages += 1
                total_words += len(words)
            
            new_files += 1
            print(f"✓ {num_pages} pages")
        
        # Calculate average document length
        self.avg_doc_len = total_words / total_pages if total_pages > 0 else 1
        self.total_pages = total_pages
        
        self.index["metadata"]["last_updated"] = datetime.now().isoformat()
        self.index["metadata"]["total_documents"] = len(self.index["documents"])
        self.index["metadata"]["total_pages"] = total_pages
        self.index["metadata"]["avg_doc_len"] = self.avg_doc_len
        
        self._save_index()
        
        print(f"\n✓ Indexing complete")
        print(f"New/Updated: {new_files}")
        print(f"Total Documents: {len(self.index['documents'])}")
        print(f"Total Pages: {total_pages}")
    
    def _remove_doc_from_word_index(self, doc_id):
        for word in list(self.index["word_index"].keys()):
            self.index["word_index"][word] = [
                loc for loc in self.index["word_index"][word]
                if loc["doc_id"] != doc_id
            ]
            if not self.index["word_index"][word]:
                del self.index["word_index"][word]
    
    def _save_index(self):
        index_to_save = {
            "documents": self.index["documents"],
            "word_index": dict(self.index["word_index"]),
            "file_hashes": self.index["file_hashes"],
            "metadata": self.index["metadata"]
        }
        
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(index_to_save, f, ensure_ascii=False)
        
        print(f"✓ Index saved: {self.index_file}")
    
    def load_index(self):
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                loaded_index = json.load(f)
                self.index = loaded_index
                self.index["word_index"] = defaultdict(list, loaded_index.get("word_index", {}))
                self.total_pages = self.index["metadata"].get("total_pages", 1)
                self.avg_doc_len = self.index["metadata"].get("avg_doc_len", 100)
            print(f"✓ Index loaded: {self.index_file}")
            return True
        except FileNotFoundError:
            print(f"✗ Index not found: {self.index_file}")
            return False
    
    def search(self, query, top_k=50):
        if not self.index:
            raise RuntimeError("Index not loaded")
        
        # Check for phrase search (quoted)
        is_phrase = query.startswith('"') and query.endswith('"')
        
        if is_phrase:
            search_term = query.strip('"')
            return self._phrase_search(search_term, top_k)
        else:
            return self._keyword_search(query, top_k)
    
    def _keyword_search(self, query, top_k):
        query_words = self.tokenize(query)
        if not query_words:
            return []
        
        results = {}
        
        for word in query_words:
            if word not in self.index["word_index"]:
                continue
            
            for location in self.index["word_index"][word]:
                doc_id = location["doc_id"]
                page_num = location["page"]
                key = (doc_id, page_num)
                
                doc = self.index["documents"][doc_id]
                page_data = next(
                    (p for p in doc["pages"] if p["page_number"] == page_num),
                    None
                )
                
                if not page_data:
                    continue
                
                # Calculate BM25 score
                tf = location["freq"]
                doc_len = page_data["word_count"]
                bm25_score = self._calculate_bm25_score(word, tf, doc_len)
                
                if key in results:
                    results[key]["score"] += bm25_score
                    # Add word to matched words
                    if word not in results[key]["matched_words"]:
                        results[key]["matched_words"].append(word)
                else:
                    results[key] = {
                        "document": doc["filename"],
                        "path": doc["path"],
                        "page": page_num,
                        "content": page_data["content"],
                        "content_lower": page_data["content_lower"],
                        "score": bm25_score,
                        "matched_words": [word]
                    }
        
        # Sort by score
        sorted_results = sorted(results.values(), key=lambda x: x["score"], reverse=True)
        
        # Extract snippets for top results
        final_results = []
        for r in sorted_results[:top_k]:
            snippet = self._extract_best_snippet(r["content"], r["content_lower"], r["matched_words"])
            final_results.append({
                "document": r["document"],
                "path": r["path"],
                "page": r["page"],
                "snippet": snippet,
                "score": round(r["score"], 4)
            })
        
        return final_results
    
    def _phrase_search(self, phrase, top_k):
        phrase_lower = phrase.lower()
        results = []
        
        for doc_id, doc in self.index["documents"].items():
            for page_data in doc["pages"]:
                content_lower = page_data.get("content_lower", page_data["content"].lower())
                
                if phrase_lower in content_lower:
                    count = content_lower.count(phrase_lower)
                    snippet = self._extract_phrase_snippet(page_data["content"], content_lower, phrase_lower)
                    
                    results.append({
                        "document": doc["filename"],
                        "path": doc["path"],
                        "page": page_data["page_number"],
                        "snippet": snippet,
                        "score": count * 10.0
                    })
        
        sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
        return sorted_results[:top_k]
    
    def _extract_best_snippet(self, content, content_lower, matched_words, context_chars=200):
        """Extract the best snippet containing matched words"""
        best_pos = -1
        best_word = matched_words[0] if matched_words else ""
        
        # Find the position with most matched words nearby
        for word in matched_words:
            pos = content_lower.find(word)
            if pos != -1:
                best_pos = pos
                best_word = word
                break
        
        if best_pos == -1:
            return content[:300] + "..." if len(content) > 300 else content
        
        # Extract context around the match
        start = max(0, best_pos - context_chars)
        end = min(len(content), best_pos + len(best_word) + context_chars)
        
        # Adjust to word boundaries
        if start > 0:
            space_pos = content.find(' ', start)
            if space_pos != -1 and space_pos < best_pos:
                start = space_pos + 1
        
        if end < len(content):
            space_pos = content.rfind(' ', best_pos, end)
            if space_pos != -1:
                end = space_pos
        
        snippet = content[start:end].strip()
        
        # Add ellipsis
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
        
        return snippet
    
    def _extract_phrase_snippet(self, content, content_lower, phrase_lower, context_chars=200):
        """Extract snippet for phrase search"""
        pos = content_lower.find(phrase_lower)
        
        if pos == -1:
            return content[:300] + "..." if len(content) > 300 else content
        
        start = max(0, pos - context_chars)
        end = min(len(content), pos + len(phrase_lower) + context_chars)
        
        # Adjust to word boundaries
        if start > 0:
            space_pos = content.find(' ', start)
            if space_pos != -1 and space_pos < pos:
                start = space_pos + 1
        
        if end < len(content):
            space_pos = content.rfind(' ', pos, end)
            if space_pos != -1:
                end = space_pos
        
        snippet = content[start:end].strip()
        
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
        
        return snippet