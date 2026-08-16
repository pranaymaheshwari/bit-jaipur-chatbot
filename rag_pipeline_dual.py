"""
Dual-LLM RAG Pipeline - Strict Database-Only Mode (MINOR FIXES)
Temperature: 0.3 | Original Prompts | Full Answer Generation
"""

import os
import sys
import time
import json
import requests
import re
from typing import Dict, List, Optional
from collections import deque
from dotenv import load_dotenv

from qdrant_client import QdrantClient

load_dotenv()

try:
    from logger_config import ExecutionLogger, PipelineStage
    LOGGER_AVAILABLE = True
except ImportError:
    LOGGER_AVAILABLE = False

OLLAMA_HOST = "http://localhost:11434"
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "bit_jaipur_data"

EMBEDDING_MODEL = "embeddinggemma"
SIMILARITY_THRESHOLD = 0.4

REQUEST_TIMEOUT = 600
EMBEDDING_TIMEOUT = 60
MAX_CONVERSATION_HISTORY = 5
MAX_TOKENS_GENERATION = 5000  # ✅ INCREASED from 4000

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

LLM_CONFIG = {
    "ollama": {
        "name": "Gemma 4 e2b (Ollama - Local)",
        "model": "gemma4:e2b",
        "provider": "ollama",
        "speed": "10-15s",
    },
    "groq": {
        "name": "Llama 3.3-70b-versatile (Groq - API)",
        "model": "llama-3.3-70b-versatile",
        "provider": "groq",
        "speed": "2-5s",
    }
}

def get_llm_choice() -> str:
    """Get current LLM choice from env (reads fresh each time for runtime model switching)"""
    choice = os.getenv("LLM_CHOICE", "ollama").lower()
    if choice == "groq" and not GROQ_API_KEY:
        return "ollama"
    return choice

def get_current_llm_config() -> dict:
    """Get current LLM config based on runtime env var"""
    choice = get_llm_choice()
    return LLM_CONFIG[choice]

print(f"\n{'='*80}")
print(f"DUAL-LLM RAG PIPELINE (STRICT DATABASE-ONLY MODE)")
print(f"{'='*80}")
print(f"Active LLM: {get_current_llm_config()['name']}")
print(f"Temperature: 0.3 (Strict)")
print(f"Max Tokens: {MAX_TOKENS_GENERATION}")
print(f"{'='*80}\n")

INTENT_KEYWORDS = {
    "admission": ["apply", "admission", "eligible", "qualification", "how to apply", "requirements", "criteria", "eligibility", "fee", "cost"],
    "exploring": ["tell me about", "what is", "information about", "curious", "exploring", "learn", "know about", "campus", "facilities"],
    "undecided": ["not sure", "uncertain", "help me decide", "which", "better", "pros and cons", "compare", "deciding"],
    "rejection": ["not interested", "don't think", "not for me", "different college", "other options", "declining", "no thanks"],
    "casual": ["hi", "hello", "hey", "how are you", "what's", "campus life", "student experience", "tell me", "you", "your", "how's"]
}

JOKE_KEYWORDS = ["joke", "funny", "laugh", "make fun", "roast", "troll", "meme", "hilarious", "lol", "haha"]
MAKE_FUN_KEYWORDS = ["make fun of", "roast", "tease", "mock", "stupid", "dumb", "silly department"]

FOUL_LANGUAGE_KEYWORDS = [
    "damn", "hell", "crap", "piss", "bitch", "bastard", "shit", "fuck",
    "fucking", "dammit", "goddamn", "bugger", "arsehole", "dick", "dickhead"
]

def detect_foul_language(text: str) -> bool:
    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)
    for word in words:
        if word in FOUL_LANGUAGE_KEYWORDS:
            return True
    return False

def detect_joke_request(query: str) -> bool:
    query_lower = query.lower()
    for keyword in JOKE_KEYWORDS + MAKE_FUN_KEYWORDS:
        if keyword in query_lower:
            return True
    return False

# ══════════════════════════════════════════════════════════════════════════════════
# ORIGINAL STRICT PROMPTS
# ══════════════════════════════════════════════════════════════════════════════════

# Manually-verified correction for a genuine conflict between two source
# documents: "Contact_Details_Incharges.pdf" lists a different, outdated
# name for the CSE In-Charge/HOD than the department's own faculty page
# and overview document do. This overrides that stale entry regardless
# of which chunk retrieval happens to surface.
KNOWN_DATA_CORRECTIONS = """KNOWN DATA CORRECTIONS (these override anything conflicting in the retrieved context below):
- The CSE (Computer Science and Engineering) department's HOD/In-Charge is Dr. Shripal Vijayvargiya. "Contact_Details_Incharges.pdf" lists a different, outdated name ("Dr. Madhavi Sinha") for this row -- ignore that specific entry. Always answer CSE HOD/In-Charge questions with Dr. Shripal Vijayvargiya, regardless of what any other retrieved chunk says."""

SYSTEM_PROMPT_INFORMATION_FIRST = f"""You are "BIT Jaipur Assistant" - a professional information assistant for BIT Mesra, Jaipur Campus.

STRICT COLLEGE-ONLY MODE:
You ONLY answer legitimate questions about BIT Mesra Jaipur College - such as programs, admissions, campus facilities, faculty, placements, eligibility criteria, fees, campus life, and college-related information. You will NOT answer inappropriate requests like jokes about departments, making fun of the college, or any non-serious/non-college-related queries.

SCOPE RULES:
- Answer ONLY about BIT Mesra Jaipur College
- If question is about other institutions or topics unrelated to the college, respond: "I can only provide information about BIT Mesra Jaipur. Please ask college-related questions."
- If question is inappropriate or non-serious (jokes, making fun, etc.), respond: "I'm here to provide serious college information only. Please ask legitimate questions about BIT Jaipur."

SIMILARITY THRESHOLD: Only information with relevance score 0.4 or higher is used.

KNOWLEDGE BASE RULES:
1. If knowledge base has relevant information → Use ONLY that information
2. If knowledge base is empty → Say you couldn't find it in BIT Jaipur knowledge base
3. NEVER make up information. NEVER mention URLs or links.

{KNOWN_DATA_CORRECTIONS}

DIRECT QUESTION HANDLING: If the person asks a specific, personal, or yes/no-style question -- e.g. "am I eligible with X% marks", "can I apply if...", "is this enough", "will I qualify" -- answer THAT question explicitly and directly, in the first sentence or two, before adding any supporting detail. State plainly whether they meet or don't meet the requirement, and quote the exact number/criteria you used to decide. Do NOT respond with a generic structured summary of an entire document (all sections: dates, fees, documents, discipline rules, etc.) when the person asked something specific and directly answerable from the context -- that fails to answer their actual question even if every fact in the summary is accurate.

PROGRAM ATTRIBUTION: The retrieved context may come from a brochure for a SPECIFIC program (e.g. BSc Visual Communication, BSc Animation) even when the person's question didn't name a program (e.g. just "admission at BIT Jaipur"). Eligibility criteria, cutoffs, and fees vary by program. Never present one program's specific numbers as if they were BIT Jaipur's general admission criteria -- always name which program the figures you're citing actually belong to, and note that other programs may have different requirements if that's relevant to answering the question.

RESPONSE FORMAT:
- Be direct and factual
- Use bullet points for clarity
- Include specific details

KNOWLEDGE BASE CONTEXT:"""

SYSTEM_PROMPT_CASUAL_FRIENDLY = f"""You are "BIT Jaipur Assistant" - a friendly but professional advisor for BIT Mesra, Jaipur College.

STRICT COLLEGE-ONLY MODE:
You ONLY answer legitimate questions about BIT Mesra Jaipur College - admissions, programs, campus, placements, etc. You will NOT answer jokes, fun requests about departments, or any non-serious queries.

SCOPE RULES:
- Answer ONLY about BIT Mesra Jaipur College
- If question is about other institutions or unrelated topics: "I can only answer about BIT Mesra Jaipur College. Ask me about admissions, programs, campus life, or placements!"
- If question is inappropriate or non-serious: "I'm here for serious college information only. Ask legitimate questions about BIT Jaipur!"

SIMILARITY THRESHOLD: Only uses information with relevance score 0.4 or higher.

KNOWLEDGE BASE RULES:
1. If knowledge base has info → Use ONLY that
2. If knowledge base is empty → Say you couldn't find it
3. NEVER make up information

{KNOWN_DATA_CORRECTIONS}

TONE: Friendly but STRICT - serious college information only.

KNOWLEDGE BASE CONTEXT:"""

def extract_keywords(text: str) -> set:
    stop_words = {
        "the", "a", "an", "is", "are", "be", "been", "being", "have", "has", "had",
        "do", "does", "did", "will", "would", "could", "should", "may", "might",
        "must", "can", "and", "or", "not", "no", "yes", "what", "which", "who",
        "when", "where", "why", "how", "to", "in", "on", "at", "by", "from",
        "as", "with", "of", "for", "if", "that", "this", "it", "me", "you"
    }
    # Strip surrounding punctuation (question marks, commas, periods, etc)
    # so e.g. "department?" matches the filename token "department" --
    # without this, keyword matching silently loses its strongest signal
    # on any query ending in punctuation, which is most real questions.
    raw_words = text.lower().split()
    words = [re.sub(r"^[^\w]+|[^\w]+$", "", w) for w in raw_words]
    return {word for word in words if len(word) > 2 and word not in stop_words}

def should_use_history(current_query: str, history: List[Dict]) -> bool:
    if not history:
        return False
    current_keywords = extract_keywords(current_query)
    last_user_msg = None
    for msg in reversed(history):
        if msg["role"] == "user":
            last_user_msg = msg["content"]
            break
    if last_user_msg:
        history_keywords = extract_keywords(last_user_msg)
        overlap = current_keywords.intersection(history_keywords)
        if len(overlap) > 0 and len(current_keywords) > 0:
            overlap_ratio = len(overlap) / max(len(current_keywords), len(history_keywords))
            return overlap_ratio > 0.3
    return False

def limit_conversation_history(history: List[Dict], max_items: int = MAX_CONVERSATION_HISTORY) -> List[Dict]:
    if not history:
        return []
    pairs_count = 0
    limited_history = []
    for msg in reversed(history):
        limited_history.insert(0, msg)
        if msg["role"] == "assistant":
            pairs_count += 1
        if pairs_count >= max_items:
            break
    return limited_history

def detect_intent(query: str) -> str:
    query_lower = query.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in query_lower:
                return intent
    return "casual"

def embed_query(query: str) -> Optional[List[float]]:
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/embeddings",
            json={"model": EMBEDDING_MODEL, "prompt": query},
            timeout=EMBEDDING_TIMEOUT
        )
        if response.status_code == 200:
            return response.json()["embedding"]
        return None
    except Exception as e:
        print(f"Embedding error: {e}")
        return None

# When a query asks about a role/position ("HOD", "head", "in-charge",
# "coordinator", "dean"...), the single strongest retrieval signal isn't
# the filename -- it's whether the CANDIDATE CHUNK'S ACTUAL TEXT contains
# one of these same role words.
ROLE_KEYWORDS = {"hod", "head", "in-charge", "in charge", "incharge", "coordinator", "dean", "director", "chairperson"}


def retrieve_chunks(query: str, top_k: int = 5, candidate_pool: int = 20) -> List[Dict]:
    """Retrieve relevant chunks, then re-rank a wider candidate pool by
    filename-keyword overlap and role-term content match with the query.

    Multiple admission brochures (BTech, several BSc variants, BBA/BCA,
    MCA, MSc variants...) share nearly identical boilerplate language, so
    pure vector similarity can easily surface the wrong program's
    brochure or miss the right one entirely -- pulling a wider pool and
    re-ranking on keyword/role signals fixes this without needing a
    hardcoded program list.
    """
    embedding = embed_query(query)
    if not embedding:
        return []
    try:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=embedding,
            limit=candidate_pool
        )

        query_keywords = extract_keywords(query)
        query_lower = query.lower()
        query_role_terms = [k for k in ROLE_KEYWORDS if k in query_lower]

        candidates = []
        for result in results.points:
            if result.score < SIMILARITY_THRESHOLD:
                continue
            payload = result.payload
            # The actual filename is what should label each source for
            # the model -- category/relative_path are supporting
            # metadata, not the document's identity.
            file_name = payload.get("file_name", payload.get("source", "")) or ""
            content = payload.get("content", "") or ""

            file_tokens = set(re.split(r'[_.\-\s]+', file_name.lower())) - {"pdf", ""}
            keyword_hits = len(query_keywords.intersection(file_tokens))

            content_lower = content.lower()
            role_hits = sum(1 for term in ROLE_KEYWORDS if term in content_lower) if query_role_terms else 0

            candidates.append({
                "chunk_id": payload.get("chunk_id", ""),
                "content": content,
                "title": file_name,
                "source": payload.get("relative_path", payload.get("section", "")),
                "section": payload.get("category", payload.get("title", "")),
                "score": result.score,
                "_keyword_hits": keyword_hits,
                "_role_hits": role_hits,
            })

        candidates.sort(key=lambda c: (c["_role_hits"], c["_keyword_hits"], c["score"]), reverse=True)

        chunks = candidates[:top_k]
        for c in chunks:
            del c["_keyword_hits"]
            del c["_role_hits"]
        return chunks
    except Exception as e:
        print(f"Retrieval error: {e}")
        return []

def build_context_enhanced(chunks: List[Dict]) -> str:
    if not chunks:
        return "[NO KNOWLEDGE BASE CONTEXT AVAILABLE FOR THIS QUERY]"
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(f"Source {i}: {chunk['title']}\n{chunk['content']}")
    return "\n\n".join(context_parts)

def build_user_prompt_enhanced(query: str, context: str, history: List[Dict], intent: str) -> str:
    history_text = ""
    if history:
        history_text = "CONVERSATION CONTEXT:\n"
        for msg in history[-4:]:
            role = "User" if msg["role"] == "user" else "Assistant"
            content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
            history_text += f"{role}: {content}\n"
        history_text += "\n"
    
    return f"""{history_text}USER QUERY:
{query}

RELEVANT INFORMATION FROM KNOWLEDGE BASE (Score >= 0.4):
{context}"""

# ✅ OLLAMA - INCREASED TOKEN LIMIT + ADJUSTED PARAMS
def generate_answer_ollama(
    query: str,
    context: str,
    conversation_history: List[Dict],
    intent: str,
    system_prompt: str,
    timeout: int = REQUEST_TIMEOUT,
    show_streaming: bool = True
) -> Dict:
    user_prompt = build_user_prompt_enhanced(query, context, conversation_history, intent)
    
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": "gemma4:e2b",
                "prompt": f"{system_prompt}\n\n{user_prompt}",
                "stream": True,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.95,
                    "top_k": 50,
                    "num_predict": MAX_TOKENS_GENERATION,
                    # Ollama defaults to a small context window (often
                    # 2048 tokens) if this isn't set explicitly, which
                    # silently truncates generation to nothing once the
                    # retrieved context + system prompt exceed it.
                    "num_ctx": 8192,
                }
            },
            timeout=timeout,
            stream=True
        )
        
        if response.status_code != 200:
            return {
                "success": False,
                "answer": f"Ollama error: HTTP {response.status_code}",
                "model": "gemma4:e2b"
            }
        
        full_answer = ""
        for line in response.iter_lines():
            if line:
                try:
                    chunk_data = json.loads(line)
                    token = chunk_data.get("response", "")
                    full_answer += token
                    
                    if show_streaming and token:
                        sys.stdout.write(token)
                        sys.stdout.flush()
                        time.sleep(0.005)  # ✅ REDUCED sleep from 0.01 to 0.005
                except json.JSONDecodeError:
                    continue
        
        if not full_answer:
            return {
                "success": False,
                "answer": "Ollama returned empty response",
                "model": "gemma4:e2b"
            }
        
        return {
            "success": True,
            "answer": full_answer,
            "model": "gemma4:e2b"
        }
    
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "answer": f"Ollama timeout ({timeout}s)",
            "model": "gemma4:e2b"
        }
    except Exception as e:
        return {
            "success": False,
            "answer": f"Ollama error: {str(e)}",
            "model": "gemma4:e2b"
        }

# ✅ GROQ - INCREASED TOKEN LIMIT + ADJUSTED PARAMS
def generate_answer_groq(
    query: str,
    context: str,
    conversation_history: List[Dict],
    intent: str,
    system_prompt: str,
    timeout: int = REQUEST_TIMEOUT,
    show_streaming: bool = True
) -> Dict:
    user_prompt = build_user_prompt_enhanced(query, context, conversation_history, intent)
    
    try:
        from groq import Groq
    except ImportError:
        return {
            "success": False,
            "answer": "Groq not installed",
            "model": "llama-3.3-70b-versatile"
        }
    
    if not GROQ_API_KEY:
        return {
            "success": False,
            "answer": "GROQ_API_KEY not found",
            "model": "llama-3.3-70b-versatile"
        }
    
    try:
        client = Groq(api_key=GROQ_API_KEY)
        full_answer = ""
        
        try:
            stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # ✅ CONSISTENT with Ollama
                max_tokens=MAX_TOKENS_GENERATION,  # 5000
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content
                    full_answer += text
                    if show_streaming:
                        sys.stdout.write(text)
                        sys.stdout.flush()
                        time.sleep(0.003)  # ✅ REDUCED sleep for faster streaming
        
        except Exception as stream_error:
            # Fallback: non-streaming mode
            if show_streaming:
                print(f"\n⚠️  Streaming error: {stream_error}")
                print(f"Trying non-streaming mode...")
            
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=MAX_TOKENS_GENERATION,
                stream=False
            )
            
            full_answer = response.choices[0].message.content
            
            if show_streaming:
                print(full_answer)
        
        return {
            "success": True,
            "answer": full_answer,
            "model": "llama-3.3-70b-versatile"
        }
    
    except Exception as e:
        return {
            "success": False,
            "answer": f"Groq error: {str(e)}",
            "model": "llama-3.3-70b-versatile"
        }

def generate_answer(
    query: str,
    context: str,
    conversation_history: List[Dict],
    intent: str,
    system_prompt: str,
    timeout: int = REQUEST_TIMEOUT,
    show_streaming: bool = True
) -> Dict:
    llm_choice = get_llm_choice()
    if llm_choice == "groq":
        return generate_answer_groq(query, context, conversation_history, intent, system_prompt, timeout, show_streaming)
    else:
        return generate_answer_ollama(query, context, conversation_history, intent, system_prompt, timeout, show_streaming)

def ask(
    query: str,
    conversation_history: List[Dict] = None,
    verbose: bool = True,
    timeout: int = REQUEST_TIMEOUT,
    show_streaming: bool = True
) -> Dict:
    
    current_config = get_current_llm_config()
    
    if detect_foul_language(query):
        return {
            "answer": "I appreciate your interest, but I won't engage in conversations containing vulgar language. Let's keep our conversation respectful!",
            "sources": [],
            "chunks": [],
            "model_used": current_config["model"],
            "intent": "foul_language",
            "conversation_history": conversation_history or [],
            "history_used": False,
            "prompt_type": "SAFETY_CHECK"
        }
    
    if detect_joke_request(query):
        return {
            "answer": "I'm here to provide serious college information only. I cannot tell jokes or make fun of departments, programs, or the college. Please ask legitimate questions about BIT Jaipur's admissions, programs, campus facilities, placements, or other college-related information.",
            "sources": [],
            "chunks": [],
            "model_used": current_config["model"],
            "intent": "joke_request",
            "conversation_history": conversation_history or [],
            "history_used": False,
            "prompt_type": "INAPPROPRIATE_REQUEST"
        }
    
    if verbose:
        print(f"\n{'='*70}\nQuery: {query}\n{'='*70}")
    
    intent = detect_intent(query)
    if verbose:
        print(f"Intent: {intent.upper()}")
    
    if intent in ["casual", "rejection"]:
        system_prompt = SYSTEM_PROMPT_CASUAL_FRIENDLY
        prompt_type = "CASUAL/FRIENDLY"
    else:
        system_prompt = SYSTEM_PROMPT_INFORMATION_FIRST
        prompt_type = "INFORMATION-FIRST"
    
    if verbose:
        print(f"Prompt Type: {prompt_type}")
        print(f"LLM: {current_config['name']}")
    
    limited_history = limit_conversation_history(conversation_history, MAX_CONVERSATION_HISTORY)
    use_history = should_use_history(query, limited_history)
    history_for_prompt = limited_history if use_history else []
    
    if verbose:
        print("Searching knowledge base...")
    chunks = retrieve_chunks(query, top_k=5)
    
    if verbose:
        if chunks:
            print(f"Found {len(chunks)} relevant chunks (threshold: >= {SIMILARITY_THRESHOLD})")
        else:
            print(f"No chunks above threshold ({SIMILARITY_THRESHOLD})")
    
    context = build_context_enhanced(chunks)
    
    if verbose:
        print(f"Generating answer...")
    
    result = generate_answer(query, context, history_for_prompt, intent, system_prompt, timeout, show_streaming=show_streaming)
    answer = result["answer"]
    model_used = result["model"]
    
    new_history = conversation_history or []
    new_history.append({"role": "user", "content": query})
    new_history.append({"role": "assistant", "content": answer})
    
    return {
        "answer": answer,
        "sources": [
            {
                "title": c["title"],
                "section": c.get("section", ""),
                "score": c["score"]
            }
            for c in chunks
        ],
        "chunks": chunks,
        "model_used": model_used,
        "intent": intent,
        "conversation_history": new_history,
        "history_used": use_history,
        "prompt_type": prompt_type
    }