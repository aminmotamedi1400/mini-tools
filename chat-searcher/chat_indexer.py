# chat_indexer.py
import os
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict


class ChatIndexer:
    def __init__(self, chat_directory, index_file="chat_index.json"):
        self.chat_directory = Path(chat_directory)
        self.index_file = index_file
        self.index = None
    
    def parse_chat_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            title_match = re.search(r'^#\s*\*?\*?\s*(.+?)(?:\*\*)?$', content, re.MULTILINE)
            date_match = re.search(r'\*\*Date:\*\*\s*(.+?)$', content, re.MULTILINE)
            conv_id_match = re.search(r'\*\*Conversation ID:\*\*\s*(.+?)$', content, re.MULTILINE)
            
            title = title_match.group(1).strip() if title_match else file_path.stem
            date = date_match.group(1).strip() if date_match else ""
            conv_id = conv_id_match.group(1).strip() if conv_id_match else ""
            
            messages = []
            sections = re.split(r'\n---\n', content)
            
            for section in sections:
                user_match = re.search(r'##\s*شما\s*\n(.+?)(?=\n##|\Z)', section, re.DOTALL)
                assistant_match = re.search(r'##\s*دستیار\s*\n(.+?)(?=\n##|\Z)', section, re.DOTALL)
                
                if user_match:
                    messages.append({
                        "role": "user",
                        "content": user_match.group(1).strip()
                    })
                
                if assistant_match:
                    messages.append({
                        "role": "assistant",
                        "content": assistant_match.group(1).strip()
                    })
            
            return {
                "title": title,
                "date": date,
                "conversation_id": conv_id,
                "messages": messages,
                "message_count": len(messages)
            }
            
        except Exception as e:
            print(f"✗ Error parsing {file_path.name}: {e}")
            return None
    
    def tokenize(self, text):
        text = re.sub(r'[*#`\[\]()]', ' ', text)
        return re.findall(r'\b\w+\b', text.lower())
    
    def build_index(self):
        md_files = list(self.chat_directory.glob("**/*.md"))
        
        self.index = {
            "conversations": {},
            "word_index": defaultdict(list),
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "total_conversations": 0,
                "total_messages": 0
            }
        }
        
        total_messages = 0
        
        for idx, md_path in enumerate(md_files, 1):
            print(f"Processing ({idx}/{len(md_files)}): {md_path.name}")
            
            chat_data = self.parse_chat_file(md_path)
            
            if not chat_data:
                continue
            
            doc_id = str(md_path.relative_to(self.chat_directory))
            
            self.index["conversations"][doc_id] = {
                "filename": md_path.name,
                "path": str(md_path),
                "title": chat_data["title"],
                "date": chat_data["date"],
                "conversation_id": chat_data["conversation_id"],
                "message_count": chat_data["message_count"],
                "messages": []
            }
            
            for msg_idx, message in enumerate(chat_data["messages"]):
                words = self.tokenize(message["content"])
                
                self.index["conversations"][doc_id]["messages"].append({
                    "message_number": msg_idx + 1,
                    "role": message["role"],
                    "content": message["content"],
                    "word_count": len(words)
                })
                
                for word in set(words):
                    self.index["word_index"][word].append({
                        "doc_id": doc_id,
                        "message_number": msg_idx + 1,
                        "role": message["role"]
                    })
            
            total_messages += chat_data["message_count"]
            print(f"✓ {chat_data['message_count']} messages")
        
        self.index["metadata"]["total_conversations"] = len(self.index["conversations"])
        self.index["metadata"]["total_messages"] = total_messages
        
        self._save_index()
        
        print(f"\n✓ Indexing complete")
        print(f"Conversations: {len(self.index['conversations'])}")
        print(f"Messages: {total_messages}")
        print(f"Unique words: {len(self.index['word_index'])}")
    
    def _save_index(self):
        index_to_save = {
            "conversations": self.index["conversations"],
            "word_index": dict(self.index["word_index"]),
            "metadata": self.index["metadata"]
        }
        
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(index_to_save, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Index saved: {self.index_file}")
    
    def load_index(self):
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                loaded_index = json.load(f)
                self.index = loaded_index
                self.index["word_index"] = defaultdict(list, loaded_index["word_index"])
            print(f"✓ Index loaded: {self.index_file}")
            return True
        except FileNotFoundError:
            print(f"✗ Index not found: {self.index_file}")
            return False
    
    def search(self, query):
        if not self.index:
            raise RuntimeError("Index not loaded")
        
        query_words = self.tokenize(query)
        results = []
        seen = set()
        
        for word in query_words:
            if word not in self.index["word_index"]:
                continue
            
            for location in self.index["word_index"][word]:
                doc_id = location["doc_id"]
                msg_num = location["message_number"]
                key = (doc_id, msg_num)
                
                if key in seen:
                    continue
                seen.add(key)
                
                conv = self.index["conversations"][doc_id]
                message = next(
                    (m for m in conv["messages"] if m["message_number"] == msg_num),
                    None
                )
                
                if message:
                    snippet = self._get_snippet(message["content"], word)
                    results.append({
                        "conversation": conv["title"],
                        "filename": conv["filename"],
                        "path": conv["path"],
                        "date": conv["date"],
                        "message_number": msg_num,
                        "role": message["role"],
                        "snippet": snippet
                    })
        
        return results
    
    def _get_snippet(self, text, word, context_length=150):
        word_pos = text.lower().find(word.lower())
        if word_pos == -1:
            return text[:200] + "..."
        
        start = max(0, word_pos - context_length)
        end = min(len(text), word_pos + len(word) + context_length)
        
        snippet = text[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
        
        return snippet
    
    def print_results(self, results):
        if not results:
            print("✗ No results found")
            return
        
        print(f"\n✓ {len(results)} results found\n")
        
        for idx, result in enumerate(results, 1):
            print(f"{idx}. {result['conversation']}")
            print(f"   Date: {result['date']}")
            print(f"   Message #{result['message_number']} ({result['role']})")
            print(f"   {result['snippet']}")
            print(f"   File: {result['filename']}\n")