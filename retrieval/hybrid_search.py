from rank_bm25 import BM25Okapi

class HybridRetriever:
    def __init__(self, chunks):
        self.chunks = chunks
        self.tokens = [c["content"].lower().split() for c in chunks]
        self.bm25 = BM25Okapi(self.tokens) if self.tokens else None

    def search(self, query, customer=None, top_k=6):
        if not self.chunks:
            return []
        q_tokens = query.lower().split()
        scores = self.bm25.get_scores(q_tokens) if self.bm25 else [0] * len(self.chunks)
        ranked = sorted(range(len(self.chunks)), key=lambda i: scores[i], reverse=True)
        out = []
        for i in ranked:
            c = self.chunks[i].copy()
            if customer and c.get("customer") and c["customer"] != customer:
                continue
            c["bm25_score"] = float(scores[i])
            out.append(c)
            if len(out) >= top_k:
                break
        return out
