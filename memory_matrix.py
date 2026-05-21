import os
import time
import chromadb
import threading

from config import MEMORY_VAULT, OBSIDIAN_VAULT

# The Traffic Light
db_write_lock = threading.Lock()


class VectorMemory:
    def __init__(self, storage_dir=MEMORY_VAULT, obsidian_dir=OBSIDIAN_VAULT):
        print("[SYSTEM] Initializing Persistent Vector Memory Matrix (ChromaDB Silo & Obsidian Sync Engine)...")
        self.client = chromadb.PersistentClient(path=storage_dir)
        self.obsidian_dir = obsidian_dir

    def _get_silo(self, project_name: str):
        safe_name = "".join(e for e in project_name.lower() if e.isalnum()) or "general"
        return self.client.get_or_create_collection(name=f"silo_{safe_name}")

    def _write_to_obsidian(self, project_name: str, event_summary: str, file_path: str):
        """Creates a readable Markdown file in the project's isolated folder."""
        safe_name = "".join(e for e in project_name if e.isalnum()) or "General"
        project_dir = os.path.join(self.obsidian_dir, safe_name)
        os.makedirs(project_dir, exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        md_file = os.path.join(project_dir, f"Log_{timestamp}.md")
        
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(f"# Context Log: {timestamp}\n")
            f.write(f"**Associated File:** `{file_path}`\n\n")
            f.write(f"## Summary\n{event_summary}\n")

    def memorize(self, category: str, information: str) -> str:
        """Stores a unique fact semantically so it can be retrieved by concept, not just exact keywords."""
        memory_id = f"mem_{int(time.time())}"
        try:
            with db_write_lock:
                silo = self._get_silo("general")
                silo.add(
                    documents=[information],
                    metadatas=[{"category": category, "timestamp": time.time()}],
                    ids=[memory_id]
                )
            return f"Context permanently stamped into Vector Matrix under ID: {memory_id}"
        except Exception as e:
            return f"Memory storage failure: {str(e)}"

    def recall(self, query: str) -> str:
        """Queries the vector database using semantic similarity."""
        try:
            silo = self._get_silo("general")
            results = silo.query(
                query_texts=[query],
                n_results=2 # Retrieve top 2 most contextually relevant facts
            )
            
            if not results or not results['documents'] or len(results['documents'][0]) == 0:
                return "No semantically matching historical context found in database."
                
            compiled_memories = []
            for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                compiled_memories.append(f"[{meta.get('category', 'GENERAL').upper()}]: {doc}")
                
            return "Retrieved Contextual Memory:\n" + "\n".join(compiled_memories)
        except Exception as e:
            return f"Memory matrix query failed: {str(e)}"

    def journal_workspace_event(self, project_name: str, event_summary: str, associated_file: str = "None") -> str:
        memory_id = f"mem_{int(time.time())}"
        try:
            with db_write_lock:
                silo = self._get_silo(project_name)
                silo.add(
                    documents=[event_summary],
                    metadatas=[{
                        "file_path": associated_file, 
                        "timestamp": time.time(),
                        "date_string": time.strftime("%Y-%m-%d")
                    }],
                    ids=[memory_id]
                )
            # Parallel write to the Obsidian Vault
            self._write_to_obsidian(project_name, event_summary, associated_file)
            return f"Event journaled in {project_name} silo and synced to Obsidian."
        except Exception as e:
            return f"Memory matrix failure: {str(e)}"

    def query_past_workspace(self, project_name: str, topic: str, days_ago: int = 1):
        """Searches ONLY within the isolated silo for the requested project."""
        try:
            silo = self._get_silo(project_name)
            results = silo.query(
                query_texts=[topic],
                n_results=5 
            )
            
            if not results or not results['documents'][0]:
                return []

            matched_files = []
            cutoff_time = time.time() - (days_ago * 86400) 

            for meta, doc in zip(results['metadatas'][0], results['documents'][0]):
                if meta['timestamp'] >= cutoff_time:
                    matched_files.append({
                        "path": meta['file_path'],
                        "context": doc,
                        "date": meta.get('date_string', time.strftime("%Y-%m-%d"))
                    })
            
            return matched_files
        except Exception:
            return []