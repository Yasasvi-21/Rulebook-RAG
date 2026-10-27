import json
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder

CHUNKS_PATH = "data/processed/chunks.json"

GAME_ALIASES = {
    "texas_holdem": ["texas hold'em", "hold'em", "holdem", "hold em"],
    "blackjack": ["blackjack", "black jack"],
    "monopoly": ["monopoly"],
    "catan": ["catan"],
    "rummy": ["rummy"],
    "poker": ["poker"],
}

def detect_games(question):
    q = question.lower()
    return [game for game, names in GAME_ALIASES.items() if any(n in q for n in names)]
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

    
    def search_in_game(self, question, game, k):
        # rank all chunks, keep this game's, rerank its top 10
        shortlist = [c for c in self.dense(question, k=len(self.chunks)) if c["game"] == game][:10]
        scores = self.reranker.predict([(question, c["text"]) for c in shortlist])
        order = np.argsort(scores)[::-1][:k]
        return [shortlist[i] for i in order], max(scores)


    def search_routed(self, question, k=5, per_game=2, floor=-10.0):
        named = detect_games(question)

        # 1. one game named: search only that game
        if len(named) == 1:
            chunks, _ = self.search_in_game(question, named[0], k)
            return chunks

        # 2. no game named: global top k, plus any missing games above the floor
        if not named:
            results = self.search(question, k=k)
            have = {c["game"] for c in results}
            for game in sorted({c["game"] for c in self.chunks}):
                if game in have:
                    continue
                chunks, best = self.search_in_game(question, game, per_game)
                if best > floor:
                    results.extend(chunks)
            return results

        # 3. two or more games named: a few chunks from each named game
        results = []
        for game in named:
            chunks, _ = self.search_in_game(question, game, per_game)
            results.extend(chunks)
        return results


if __name__ == "__main__":
    retriever = Retriever()
    for c in retriever.search("How many hole cards is each player dealt?"):
        print(c["id"], "|", c["text"][:100])