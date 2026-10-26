import json
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder

CHUNKS_PATH = "data/processed/chunks.json"


class Retriever:
    def __init__(self):
        # runs once: load everything retrieval needs
        with open(CHUNKS_PATH) as f:
            self.chunks = json.load(f)
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        texts = [c["text"] for c in self.chunks]
        self.vectors = self.embedder.encode(texts, normalize_embeddings=True)

    def dense(self, question, k=10):
        # stage 1: fast embedding search
        q = self.embedder.encode([question], normalize_embeddings=True)[0]
        scores = self.vectors @ q
        top = np.argsort(scores)[::-1][:k]
        return [self.chunks[i] for i in top]

    def search(self, question, k=3, candidates=10):
        # stage 2: rerank the shortlist
        shortlist = self.dense(question, k=candidates)
        pairs = [(question, c["text"]) for c in shortlist]
        scores = self.reranker.predict(pairs)
        order = np.argsort(scores)[::-1][:k]
        return [shortlist[i] for i in order]


if __name__ == "__main__":
    retriever = Retriever()
    for c in retriever.search("How many hole cards is each player dealt?"):
        print(c["id"], "|", c["text"][:100])