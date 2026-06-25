import io
import json
import os
import re
import sys

import docx
import lancedb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from my_agent.core.environment import EnvironmentConfig
from my_agent.core.cache_manager import CacheManager


if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass


class RAGManager:
    """
    Central manager for the local RAG stack.
    Supports vector search, BM25 keyword search, and hybrid RRF ranking.
    """

    _instance = None
    _model = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RAGManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_name=None):
        model_name = model_name or EnvironmentConfig.load().embedding_model
        self.model_name = model_name

        self.base_data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
        os.makedirs(self.base_data_path, exist_ok=True)
        
        self.cache = CacheManager()
        
        # Pre-load model de tang toc cho cau hoi dau tien (Eager Loading)
        self._ensure_model()

    def _ensure_model(self):
        if self._model is None:
            print(f"--- Dang khoi tao RAG Engine voi model: {self.model_name} ---")
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def get_db_connection(self, topic):
        db_path = os.path.join(self.base_data_path, topic)
        return lancedb.connect(db_path)

    def get_table(self, topic):
        db = self.get_db_connection(topic)
        table_name = f"{topic}_data"
        if table_name not in db.table_names():
            return None
        return db.open_table(table_name)

    @staticmethod
    def _tokenize(text):
        return re.findall(r"\w+", text.lower())

    def _vector_search(self, topic, query, limit=10):
        table = self.get_table(topic)
        if table is None:
            return []
        query_vec = self._ensure_model().encode(query)
        return table.search(query_vec).limit(limit).to_list()

    def _bm25_search(self, topic, query, limit=10):
        table = self.get_table(topic)
        if table is None:
            return []

        all_data = table.to_pandas()
        if all_data.empty:
            return []

        corpus = all_data["text"].tolist()
        tokenized_corpus = [self._tokenize(doc) for doc in corpus]
        tokenized_query = self._tokenize(query)

        bm25 = BM25Okapi(tokenized_corpus)
        scores = bm25.get_scores(tokenized_query)

        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:limit]
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                row = all_data.iloc[idx].to_dict()
                row["_bm25_score"] = float(scores[idx])
                results.append(row)
        return results

    @staticmethod
    def _format_metadata(doc: dict) -> str:
        ordered_labels = [
            ("year", "Nam TS"),
            ("university_code", "Truong"),
            ("source_url", "Link nguon"),
            ("source_name", "Tep"),
            ("file_type", "Loai"),
        ]

        meta_parts = []
        used_keys = set()
        for key, label in ordered_labels:
            value = doc.get(key)
            if value not in (None, ""):
                meta_parts.append(f"[{label}: {value}]")
                used_keys.add(key)

        for key, value in doc.items():
            if key in used_keys or key in {"vector", "text"} or key.startswith("_"):
                continue
            if value not in (None, ""):
                meta_parts.append(f"[{key}: {value}]")

        return " ".join(meta_parts)

    def search(self, topic, query, limit=5):
        # 1. Kiem tra cache truoc (RAG cache de lau hon: 1 tuan)
        cache_key = f"rag:{topic}"
        cached_result = self.cache.get(query, cache_key, ttl_hours=168)
        if cached_result:
            print(f"--- [RAG CACHE HIT] Su dung tri thuc cu cho: {query} ---")
            return json.loads(cached_result)

        vector_results = self._vector_search(topic, query, limit=limit * 2)
        bm25_results = self._bm25_search(topic, query, limit=limit * 2)

        k = 60
        rrf_scores = {}
        
        # Combined list for year discovery
        combined_candidates = vector_results + bm25_results
        
        # Discover the latest year in the retrieved set to apply relative boost
        max_year = 0
        for res in combined_candidates:
            y = res.get("year", 0)
            try:
                y_val = int(y)
                if y_val > max_year: max_year = y_val
            except: pass

        def calculate_boost(doc):
            y = doc.get("year", 0)
            try:
                y_val = int(y)
                # Boost documents from the most recent year
                if max_year > 0 and y_val == max_year:
                    return 1.2  # 20% boost for the latest year
                return 1.0
            except:
                return 1.0

        for rank, res in enumerate(vector_results):
            text = res.get("text", "")
            boost = calculate_boost(res)
            rrf_scores[text] = rrf_scores.get(text, 0) + (1.0 / (k + rank + 1)) * boost

        for rank, res in enumerate(bm25_results):
            text = res.get("text", "")
            boost = calculate_boost(res)
            rrf_scores[text] = rrf_scores.get(text, 0) + (1.0 / (k + rank + 1)) * boost

        sorted_results = sorted(rrf_scores.items(), key=lambda item: item[1], reverse=True)

        final_results = []
        for text, score in sorted_results[:limit]:
            original_doc = next((doc for doc in combined_candidates if doc.get("text") == text), {})
            meta_str = self._format_metadata(original_doc)
            final_text = f"{meta_str}\n{text}" if meta_str else text
            final_results.append({"text": final_text, "_rrf_score": score})

        # 2. Luu vao cache
        self.cache.set(query, cache_key, json.dumps(final_results, ensure_ascii=False))
        return final_results

    def ingest_pdf(self, file_path, topic):
        print(f"--- Dang xu ly file PDF: {file_path} cho chu de {topic} ---")
        reader = PdfReader(file_path)
        full_text = ""
        for page in reader.pages:
            full_text += (page.extract_text() or "") + "\n"
        return self.ingest_text(full_text, topic)

    def ingest_docx(self, file_path, topic):
        print(f"--- Dang xu ly file Word: {file_path} cho chu de {topic} ---")
        document = docx.Document(file_path)
        full_text = "\n".join(para.text for para in document.paragraphs)
        return self.ingest_text(full_text, topic)

    def ingest_documents(self, documents, topic, chunk_size=1000, chunk_overlap=200):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""],
        )

        all_chunks = []
        all_metadata = []

        for doc in documents:
            chunks = text_splitter.split_text(doc["text"])
            metadata = doc.get("metadata", {})
            for chunk in chunks:
                all_chunks.append(chunk)
                all_metadata.append(metadata)

        if not all_chunks:
            return 0

        embeddings = self._ensure_model().encode(all_chunks)

        data = []
        for emb, chunk, metadata in zip(embeddings, all_chunks, all_metadata):
            record = {"vector": emb.tolist(), "text": chunk}
            record.update(metadata)
            data.append(record)

        db = self.get_db_connection(topic)
        table_name = f"{topic}_data"

        if table_name in db.table_names():
            db.drop_table(table_name)

        db.create_table(table_name, data=data)
        print(f"--- Da nap thanh cong {len(all_chunks)} khoi van ban vao {topic} ---")
        return len(all_chunks)

    def append_documents(self, documents, topic, chunk_size=1000, chunk_overlap=200,
                         doc_batch_size=500, embed_batch_size=128):
        """Append new documents to an existing topic table in batches to save memory."""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""],
        )

        db = self.get_db_connection(topic)
        table_name = f"{topic}_data"
        model = self._ensure_model()
        total_chunks = 0

        # Process in document batches
        for i in range(0, len(documents), doc_batch_size):
            doc_batch = documents[i:i + doc_batch_size]
            current_chunks = []
            current_metadata = []

            for doc in doc_batch:
                chunks = text_splitter.split_text(doc["text"])
                metadata = doc.get("metadata", {})
                for chunk in chunks:
                    current_chunks.append(chunk)
                    current_metadata.append(metadata)

            if not current_chunks:
                continue

            # Encode chunks for this batch
            embeddings = model.encode(current_chunks, batch_size=embed_batch_size, show_progress_bar=False)

            data = []
            for emb, chunk, metadata in zip(embeddings, current_chunks, current_metadata):
                record = {"vector": emb.tolist(), "text": chunk}
                record.update(metadata)
                data.append(record)

            # Write batch to DB
            if table_name in db.table_names():
                table = db.open_table(table_name)
                table.add(data)
            else:
                db.create_table(table_name, data=data)

            total_chunks += len(current_chunks)
            print(f"--- [Batch {i//doc_batch_size + 1}] Da nạp {len(current_chunks)} chunks vào {topic}. Tổng: {total_chunks} ---")

        return total_chunks

    def ingest_text(self, text, topic, chunk_size=1000, chunk_overlap=200):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""],
        )
        chunks = text_splitter.split_text(text)

        if not chunks:
            return 0

        embeddings = self._ensure_model().encode(chunks)

        data = [{"vector": emb.tolist(), "text": chunk} for emb, chunk in zip(embeddings, chunks)]

        db = self.get_db_connection(topic)
        table_name = f"{topic}_data"

        if table_name in db.table_names():
            db.drop_table(table_name)

        db.create_table(table_name, data=data)
        print(f"--- Da nap thanh cong {len(chunks)} doan van ban vao {topic} ---")
        return len(chunks)

    def embed_text(self, texts):
        return self._ensure_model().encode(texts, show_progress_bar=True)
