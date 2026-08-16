"""
⚠️  DEPRECATED - USE rag_pipeline_dual.py INSTEAD ⚠️

This file is no longer used. The model routing logic has been integrated
directly into rag_pipeline_dual.py which now:
  - Reads LLM_CHOICE from env var at runtime (not import time)
  - Has non-streaming fallback for Groq
  - Uses consistent temperature=0.3 across both models
  - Properly handles payload key names from Qdrant

All functionality is duplicated in rag_pipeline_dual.py. Keep for reference only.
"""

import sys
import time
import json
import requests
from typing import Dict, List
from model_manager import model_manager

# ══════════════════════════════════════════════════════════════════════════════════
# OLLAMA GENERATOR
# ══════════════════════════════════════════════════════════════════════════════════

def generate_answer_ollama(
    query: str,
    context: str,
    conversation_history: List[Dict],
    intent: str,
    system_prompt: str,
    timeout: int = 600,
    show_streaming: bool = True
) -> Dict:
    """Generate answer using Ollama (Gemma 4 e2b)"""
    
    # LAZY IMPORT to avoid circular import with rag_pipeline.py
    from rag_pipeline_dual import build_user_prompt_enhanced
    
    user_prompt = build_user_prompt_enhanced(query, context, conversation_history, intent)
    ollama_host = "http://localhost:11434"
    current_model = "gemma4:e2b"
    
    try:
        response = requests.post(
            f"{ollama_host}/api/generate",
            json={
                "model": current_model,
                "prompt": f"{system_prompt}\n\n{user_prompt}",
                "stream": True,
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "num_predict": 2000
            },
            timeout=timeout,
            stream=True
        )
        
        if response.status_code == 200:
            full_answer = ""
            
            if show_streaming:
                print("\n" + "="*70)
                print("📝 ANSWER GENERATION (LIVE STREAMING - OLLAMA)")
                print("="*70)
            
            for line in response.iter_lines():
                if line:
                    try:
                        chunk_data = json.loads(line)
                        token = chunk_data.get("response", "")
                        full_answer += token
                        
                        if show_streaming and token:
                            sys.stdout.write(token)
                            sys.stdout.flush()
                            time.sleep(0.01)
                    
                    except json.JSONDecodeError:
                        continue
            
            if show_streaming:
                print("\n" + "="*70)
            
            return {
                "success": True,
                "answer": full_answer,
                "model": current_model
            }
        else:
            return {
                "success": False,
                "answer": f"HTTP Error {response.status_code}",
                "model": current_model
            }
    
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "answer": f"Timeout ({timeout}s exceeded)",
            "model": current_model
        }
    except Exception as e:
        return {
            "success": False,
            "answer": f"Error: {str(e)}",
            "model": current_model
        }

# ══════════════════════════════════════════════════════════════════════════════════
# GROQ GENERATOR - FIXED API CALL
# ══════════════════════════════════════════════════════════════════════════════════

def generate_answer_groq(
    query: str,
    context: str,
    conversation_history: List[Dict],
    intent: str,
    system_prompt: str,
    timeout: int = 600,
    show_streaming: bool = True
) -> Dict:
    """Generate answer using Groq API (Llama 3.3-70b-versatile)
    
    FIXED: Uses correct Groq API: client.chat.completions.create(stream=True, ...)
    Previously was using client.messages.stream() which is Anthropic/Claude API!
    """
    
    # LAZY IMPORT to avoid circular import with rag_pipeline.py
    from rag_pipeline_dual import build_user_prompt_enhanced
    
    user_prompt = build_user_prompt_enhanced(query, context, conversation_history, intent)
    
    try:
        try:
            from groq import Groq
        except ImportError:
            return {
                "success": False,
                "answer": "❌ Groq library not installed. Run: pip install groq",
                "model": "llama-3.3-70b-versatile"
            }
        
        if not model_manager.groq_api_key:
            return {
                "success": False,
                "answer": "❌ Groq API key not found. Add GROQ_API_KEY to .env file",
                "model": "llama-3.3-70b-versatile"
            }
        
        client = Groq(api_key=model_manager.groq_api_key)
        
        full_answer = ""
        
        if show_streaming:
            print("\n" + "="*70)
            print("📝 ANSWER GENERATION (LIVE STREAMING - GROQ)")
            print("="*70)
        
        try:
            # ✅ FIXED: Use correct Groq API - chat.completions.create with stream=True
            # Previously was using client.messages.stream() which is Anthropic API
            stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000,
                stream=True  # Enable streaming
            )
            
            # Iterate through streaming chunks
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content
                    full_answer += text
                    
                    if show_streaming:
                        sys.stdout.write(text)
                        sys.stdout.flush()
                        time.sleep(0.005)
        
        except Exception as stream_error:
            print(f"\n⚠️  Streaming error: {stream_error}")
            print(f"Trying non-streaming mode...")
            
            # Fallback: non-streaming
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000,
                    stream=False
                )
                
                full_answer = response.choices[0].message.content
                
                if show_streaming:
                    print(full_answer)
            
            except Exception as fallback_error:
                return {
                    "success": False,
                    "answer": f"Groq Error: {str(fallback_error)}",
                    "model": "llama-3.3-70b-versatile"
                }
        
        if show_streaming:
            print("\n" + "="*70)
        
        if not full_answer:
            return {
                "success": False,
                "answer": "No answer generated from Groq API",
                "model": "llama-3.3-70b-versatile"
            }
        
        return {
            "success": True,
            "answer": full_answer,
            "model": "llama-3.3-70b-versatile"
        }
    
    except Exception as e:
        return {
            "success": False,
            "answer": f"❌ Groq Error: {str(e)}",
            "model": "llama-3.3-70b-versatile"
        }

# ══════════════════════════════════════════════════════════════════════════════════
# SMART ROUTER - Calls appropriate generator based on CURRENT model
# ══════════════════════════════════════════════════════════════════════════════════

def generate_answer(
    query: str,
    context: str,
    conversation_history: List[Dict],
    intent: str,
    system_prompt: str,
    timeout: int = 600,
    show_streaming: bool = True
) -> Dict:
    """
    Smart router that switches models at runtime.
    
    Checks model_manager.current_model and routes to appropriate generator.
    This allows Streamlit UI to change the model dynamically!
    """
    
    current_model = model_manager.get_current_model()
    
    if current_model == "gemma4:e2b":
        return generate_answer_ollama(
            query, context, conversation_history, intent, 
            system_prompt, timeout, show_streaming
        )
    elif current_model == "llama-3.3-70b-versatile":
        return generate_answer_groq(
            query, context, conversation_history, intent, 
            system_prompt, timeout, show_streaming
        )
    else:
        return {
            "success": False,
            "answer": f"Unknown model: {current_model}",
            "model": current_model
        }