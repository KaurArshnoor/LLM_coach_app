#!/usr/bin/env python3
"""Minimal FastAPI server for coaching app"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from engine import Engine
from config import DB_URL, GROK_API_KEY

app = FastAPI(title="Coaching App", version="1.0")

# CORS
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Config
DB_URL = f"postgresql://postgres:postgres@localhost/coaching_app_db"
GROK_KEY = os.getenv("GROK_API_KEY", "")

# Engine
engine = None

@app.on_event("startup")
async def startup():
    global engine
    engine = Engine(DB_URL, GROK_KEY)

@app.on_event("shutdown")
async def shutdown():
    engine.close()

# Models
class RecommendationRequest(BaseModel):
    query: str
    user_id: str = None
    top_k: int = 5

class HealthResponse(BaseModel):
    status: str
    grok_configured: bool

# Endpoints
@app.get("/", tags=["Meta"])
async def root():
    return {"status": "ok", "message": "LLM Coaching App backend online"}

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    # Return 204 to avoid a 404 when favicon is not provided
    from fastapi import Response
    return Response(status_code=204)

@app.get("/health", response_model=HealthResponse)
async def health():
    return {"status": "healthy", "grok_configured": bool(GROK_KEY)}

@app.post("/recommend")
async def get_recommendations(req: RecommendationRequest):
    """Get exercise recommendations"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    try:
        result = engine.recommend(req.query, req.user_id, req.top_k)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/exercises/{exercise_id}")
async def get_exercise(exercise_id: str):
    """Get exercise details"""
    cursor = engine.conn.cursor(cursor_factory=__import__('psycopg2').extras.RealDictCursor)
    cursor.execute("SELECT * FROM exercises WHERE id = %s", (exercise_id,))
    result = cursor.fetchone()
    cursor.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return dict(result)

@app.post("/users/onboard")
async def onboard_user(data: dict):
    """Create/update user profile"""
    cursor = engine.conn.cursor()
    cursor.execute(
        """INSERT INTO user_profiles (user_id, goals, constraints, preferences) 
           VALUES (%s, %s, %s, %s) 
           ON CONFLICT (user_id) DO UPDATE SET goals = EXCLUDED.goals, constraints = EXCLUDED.constraints, preferences = EXCLUDED.preferences""",
        (data.get('user_id'), data.get('goals'), data.get('constraints'), data.get('preferences'))
    )
    engine.conn.commit()
    cursor.close()
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
