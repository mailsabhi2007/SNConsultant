"""Semantic cache for reducing LLM API calls."""

import json
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple, List
from database import get_db_connection
from knowledge_base import get_embeddings


def get_query_embedding(query: str) -> bytes:
    """
    Get embedding for a query.
    
    Args:
        query: Query text
        
    Returns:
        Embedding as bytes (for storage in SQLite BLOB)
    """
    embeddings = get_embeddings()
    embedding_vector = embeddings.embed_query(query)
    
    # Convert to numpy array and then to bytes
    embedding_array = np.array(embedding_vector, dtype=np.float32)
    return embedding_array.tobytes()


def cosine_similarity(embedding1: bytes, embedding2: bytes) -> float:
    """
    Calculate cosine similarity between two embeddings.
    
    Args:
        embedding1: First embedding as bytes
        embedding2: Second embedding as bytes
        
    Returns:
        Cosine similarity score (0-1)
    """
    vec1 = np.frombuffer(embedding1, dtype=np.float32)
    vec2 = np.frombuffer(embedding2, dtype=np.float32)
    
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def is_query_cacheable(query: str) -> bool:
    """
    Determine if a query should be cached.
    
    Only "how-to" type questions should be cached. Live instance analysis
    questions should never be cached as they require current data.
    
    Args:
        query: User query text
        
    Returns:
        True if query is cacheable, False otherwise
    """
    query_lower = query.lower()
    
    # Keywords that indicate live instance analysis (NOT cacheable)
    live_instance_keywords = [
        'check my', 'my instance', 'my system', 'current', 'recent',
        'what is the', 'show me the', 'get the', 'fetch the',
        'error log', 'recent changes', 'current value', 'live data',
        'check the', 'what are the', 'list the', 'display the',
        'schema', 'table structure', 'syslog', 'sys_update_xml',
        'connect to', 'live instance', 'actual configuration'
    ]
    
    # Keywords that indicate how-to questions (cacheable)
    how_to_keywords = [
        'how to', 'how do i', 'how can i', 'what is', 'explain',
        'best practice', 'recommendation', 'should i', 'what are',
        'guide', 'tutorial', 'example', 'documentation'
    ]
    
    # Check for live instance keywords first (higher priority)
    for keyword in live_instance_keywords:
        if keyword in query_lower:
            return False
    
    # Check for how-to keywords
    for keyword in how_to_keywords:
        if keyword in query_lower:
            return True
    
    # Default: if query asks about current state or specific instance data, don't cache
    # Otherwise, assume it's a general how-to question
    if any(word in query_lower for word in ['my', 'current', 'recent', 'now', 'today']):
        return False
    
    # Default to cacheable for general knowledge questions
    return True


def check_cache(
    query: str,
    user_id: Optional[str] = None,
    similarity_threshold: float = 0.75,
    model_name: Optional[str] = None,
    temperature: Optional[float] = None
) -> Optional[Dict[str, Any]]:
    """
    Check if a semantically similar query exists in cache.
    
    Only checks cache if query is determined to be cacheable (how-to questions).
    Live instance analysis questions are never cached.
    
    Args:
        query: Query text
        user_id: Optional user ID for user-specific cache
        similarity_threshold: Minimum similarity score (0-1), default 0.75
        model_name: Optional model name filter
        temperature: Optional temperature filter
        
    Returns:
        Cached response if found, None otherwise
    """
    # Only check cache for cacheable queries
    if not is_query_cacheable(query):
        # Debug: Log why query is not cacheable
        try:
            import json
            import time
            with open(r"c:\Users\Kajal Gupta\SN Consultant\.cursor\debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"CACHE_SKIP","location":"semantic_cache.py:128","message":"Query not cacheable","data":{"query":query[:100],"user_id":user_id},"timestamp":int(time.time()*1000)})+"\n")
        except: pass
        return None
    
    query_embedding = get_query_embedding(query)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get relevant cache entries
        if user_id:
            if model_name and temperature is not None:
                cursor.execute("""
                    SELECT cache_id, query_embedding, query_text, response_text, 
                           metadata, expires_at
                    FROM semantic_cache
                    WHERE user_id = ? AND model_name = ? AND temperature = ?
                    AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                """, (user_id, model_name, temperature))
            elif model_name:
                cursor.execute("""
                    SELECT cache_id, query_embedding, query_text, response_text,
                           metadata, expires_at
                    FROM semantic_cache
                    WHERE user_id = ? AND model_name = ?
                    AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                """, (user_id, model_name))
            else:
                cursor.execute("""
                    SELECT cache_id, query_embedding, query_text, response_text,
                           metadata, expires_at
                    FROM semantic_cache
                    WHERE user_id = ?
                    AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                """, (user_id,))
        else:
            # Global cache (user_id is NULL)
            if model_name and temperature is not None:
                cursor.execute("""
                    SELECT cache_id, query_embedding, query_text, response_text,
                           metadata, expires_at
                    FROM semantic_cache
                    WHERE user_id IS NULL AND model_name = ? AND temperature = ?
                    AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                """, (model_name, temperature))
            elif model_name:
                cursor.execute("""
                    SELECT cache_id, query_embedding, query_text, response_text,
                           metadata, expires_at
                    FROM semantic_cache
                    WHERE user_id IS NULL AND model_name = ?
                    AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                """, (model_name,))
            else:
                cursor.execute("""
                    SELECT cache_id, query_embedding, query_text, response_text,
                           metadata, expires_at
                    FROM semantic_cache
                    WHERE user_id IS NULL
                    AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                """)
        
        # Check similarity for each cached entry
        best_match = None
        best_similarity = 0.0
        total_checked = 0
        
        for row in cursor.fetchall():
            total_checked += 1
            cached_embedding = row[1]
            cached_query = row[2]
            
            # First check for exact text match (case-insensitive, whitespace normalized)
            query_normalized = ' '.join(query.strip().lower().split())
            cached_query_normalized = ' '.join(cached_query.strip().lower().split())
            
            if query_normalized == cached_query_normalized:
                # Exact match - use it immediately
                best_match = {
                    'cache_id': row[0],
                    'query_text': row[2],
                    'response_text': row[3],
                    'metadata': json.loads(row[4]) if row[4] else {},
                    'similarity': 1.0,  # Exact match = 100% similarity
                    'expires_at': row[5],
                    'is_cached': True
                }
                best_similarity = 1.0
                break  # Exact match found, no need to check others
            
            # Otherwise check semantic similarity
            similarity = cosine_similarity(query_embedding, cached_embedding)
            
            if similarity > best_similarity and similarity >= similarity_threshold:
                best_similarity = similarity
                best_match = {
                    'cache_id': row[0],
                    'query_text': row[2],
                    'response_text': row[3],
                    'metadata': json.loads(row[4]) if row[4] else {},
                    'similarity': similarity,
                    'expires_at': row[5],
                    'is_cached': True  # Flag to indicate this is from cache
                }
        
        # Debug: Log cache check results
        try:
            import json
            import time
            with open(r"c:\Users\Kajal Gupta\SN Consultant\.cursor\debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"CACHE_SEARCH","location":"semantic_cache.py:195","message":"Cache search completed","data":{"user_id":user_id,"total_checked":total_checked,"best_similarity":best_similarity,"cache_hit":bool(best_match),"threshold":similarity_threshold},"timestamp":int(time.time()*1000)})+"\n")
        except: pass
        
        # Update hit count if match found
        if best_match:
            cursor.execute("""
                UPDATE semantic_cache
                SET hit_count = hit_count + 1,
                    last_used = CURRENT_TIMESTAMP
                WHERE cache_id = ?
            """, (best_match['cache_id'],))
        
        return best_match


def store_cache(
    query: str,
    response: str,
    user_id: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None,
    ttl_days: int = 15
) -> Optional[int]:
    """
    Store a query-response pair in cache.
    
    Only stores cache if query is determined to be cacheable (how-to questions).
    Live instance analysis questions are never cached.
    
    Args:
        query: Query text
        response: Response text
        user_id: Optional user ID for user-specific cache
        model_name: Model name used
        temperature: Temperature used
        metadata: Optional metadata
        ttl_days: Time to live in days (default 15)
        
    Returns:
        cache_id if stored, None if query is not cacheable
    """
    # Only store cache for cacheable queries
    if not is_query_cacheable(query):
        # Debug: Log why query is not being cached
        try:
            import json
            import time
            with open(r"c:\Users\Kajal Gupta\SN Consultant\.cursor\debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"CACHE_STORE_SKIP","location":"semantic_cache.py:249","message":"Not storing in cache - query not cacheable","data":{"query":query[:100],"user_id":user_id},"timestamp":int(time.time()*1000)})+"\n")
        except: pass
        return None
    
    query_embedding = get_query_embedding(query)
    metadata_str = json.dumps(metadata) if metadata else None
    
    expires_at = None
    if ttl_days > 0:
        expires_at = datetime.now() + timedelta(days=ttl_days)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO semantic_cache (
                user_id, query_embedding, query_text, response_text,
                model_name, temperature, metadata, expires_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, query_embedding, query, response, model_name, temperature, metadata_str, expires_at))
        
        cache_id = cursor.lastrowid
        
        # Debug: Log successful cache storage
        try:
            import json
            import time
            with open(r"c:\Users\Kajal Gupta\SN Consultant\.cursor\debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"CACHE_STORED","location":"semantic_cache.py:270","message":"Successfully stored in cache","data":{"cache_id":cache_id,"user_id":user_id,"query":query[:100],"response_length":len(response)},"timestamp":int(time.time()*1000)})+"\n")
        except: pass
        
        return cache_id


def get_cache_stats(user_id: Optional[str] = None) -> Dict[str, Any]:
    """Get cache statistics."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_entries,
                    SUM(hit_count) as total_hits,
                    AVG(hit_count) as avg_hits
                FROM semantic_cache
                WHERE user_id = ?
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_entries,
                    SUM(hit_count) as total_hits,
                    AVG(hit_count) as avg_hits
                FROM semantic_cache
            """)
        
        row = cursor.fetchone()
        
        return {
            'total_entries': row[0] or 0,
            'total_hits': row[1] or 0,
            'avg_hits_per_entry': float(row[2]) if row[2] else 0.0
        }


def clear_expired_cache() -> int:
    """Clear expired cache entries. Returns number of entries deleted."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM semantic_cache
            WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP
        """)
        
        return cursor.rowcount


def clear_user_cache(user_id: str) -> int:
    """Clear all cache entries for a user. Returns number of entries deleted."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM semantic_cache
            WHERE user_id = ?
        """, (user_id,))
        
        return cursor.rowcount
