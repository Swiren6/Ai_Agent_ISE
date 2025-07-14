import json
import os
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np 
class CacheManager:
    def __init__(self, cache_path='cache.json'):
        self.cache_path = cache_path
        self.cache = self.load_cache()

    def load_cache(self):
        if os.path.exists(self.cache_path):
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_cache(self):
        with open(self.cache_path, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)

    def add_to_cache(self, question, sql, response, embedding):
        self.cache[question.strip()] = {
            "sql": sql,
            "response": response,
            "embedding": embedding.tolist()
        }
        self.save_cache()

    def find_semantically_similar_question(self, new_question_embedding, threshold=0.82):
        best_match = None
        best_similarity = 0.0

        for question, data in self.cache.items():
            cached_embedding = np.array(data.get("embedding"))
            similarity = cosine_similarity([new_question_embedding], [cached_embedding])[0][0]
            if similarity > threshold and similarity > best_similarity:
                best_similarity = similarity
                best_match = data

        return best_match
