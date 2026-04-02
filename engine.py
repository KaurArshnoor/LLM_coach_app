#!/usr/bin/env python3
"""Minimal recommendation engine with Llama LLM ranking via Groq"""
import json
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from dataclasses import dataclass
from config import DB_URL, GROK_API_KEY, DEFAULT_TOP_K, MAX_RETRIEVE

@dataclass
class Recommendation:
    id: str
    title: str
    score: float
    reasoning: str

class Engine:
    """Recommendation engine: retrieval + Llama ranking via Groq"""
    
    def __init__(self, db_url: str = DB_URL, grok_key: str = GROK_API_KEY):
        self.db_url = db_url
        self.grok_key = grok_key
        self.conn = psycopg2.connect(db_url)
    
    def retrieve(self, query: str, top_k: int = MAX_RETRIEVE) -> list:
        """Keyword search for candidates"""
        if not query or not query.strip():
            return []

        terms = [t.strip() for t in query.split() if t.strip()]
        if not terms:
            return []

        patterns = [f"%{t}%" for t in terms]

        where_parts = []
        params = []
        for p in patterns:
            where_parts.append("description ILIKE %s")
            params.append(p)
            where_parts.append("tags ILIKE %s")
            params.append(p)
            where_parts.append("title ILIKE %s")
            params.append(p)

        sql = f"""
            SELECT id, title, description, body_part, difficulty, equipment, intensity
            FROM exercises
            WHERE {' OR '.join(where_parts)}
            LIMIT %s
        """
        params.append(top_k)

        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(sql, tuple(params))
        results = cursor.fetchall()
        cursor.close()
        return results
    
    def rank_with_grok(self, query: str, exercises: list, top_k: int = 5) -> list:
        """Re-rank exercises using Llama LLM via Groq"""
        if not exercises:
            return []
        
        # Build prompt
        exercises_text = "\n".join([
            f"{i+1}. {ex['title']}: {ex['description']}"
            for i, ex in enumerate(exercises)
        ])
        
        prompt = f"""Rank these exercises by relevance to: "{query}"

{exercises_text}

Return ONLY valid JSON (no markdown, no preamble):
{{"rankings": [{{"num": 1, "score": 95, "reason": "..."}}]}}

Strict: Only rank top {top_k}. Scores 0-100."""
        
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.grok_key}"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 1000
                },
                timeout=10
            )
            
            content = response.json()['choices'][0]['message']['content']
            rankings = json.loads(content.strip())['rankings']
            
            # Map to exercises
            results = []
            for rank in rankings[:top_k]:
                idx = rank['num'] - 1
                if idx < len(exercises):
                    ex = exercises[idx]
                    results.append(Recommendation(
                        id=ex['id'],
                        title=ex['title'],
                        score=rank['score'] / 100.0,
                        reasoning=rank['reason']
                    ))
            return results
        
        except Exception as e:
            print(f"Llama error: {e}, using fallback ranking")
            return [
                Recommendation(ex['id'], ex['title'], 0.8 - i*0.1, "Fallback ranking")
                for i, ex in enumerate(exercises[:top_k])
            ]
    
    def recommend(self, query: str, user_id: str = None, top_k: int = DEFAULT_TOP_K) -> dict:
        """Get recommendations: retrieve → rank → log"""
        # Retrieve
        candidates = self.retrieve(query, top_k=20)
        
        # Rank with LLM
        recommendations = self.rank_with_grok(query, candidates, top_k)
        
        # Log
        if recommendations:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO query_logs (user_id, query, retrieved_ids, ranked_ids, response_time_ms) VALUES (%s, %s, %s, %s, %s)",
                (user_id, query, json.dumps([c['id'] for c in candidates]), 
                 json.dumps([r.id for r in recommendations]), 0)
            )
            self.conn.commit()
            cursor.close()
        
        return {
            'query': query,
            'recommendations': [
                {'rank': i+1, 'id': r.id, 'title': r.title, 'score': r.score, 'reasoning': r.reasoning}
                for i, r in enumerate(recommendations)
            ]
        }
    
    def close(self):
        self.conn.close()
