"""
Runtime Model Manager - Switch Between Ollama and Groq in Streamlit UI
"""

import os
from typing import Dict, Literal
from dotenv import load_dotenv

load_dotenv()

class ModelManager:
    """Manages model selection and configuration at runtime"""
    
    MODELS = {
        "gemma4:e2b": {
            "name": "🔵 Gemma 4 e2b (Ollama - Local)",
            "provider": "ollama",
            "model_id": "gemma4:e2b",
            "host": "http://localhost:11434",
            "description": "Fast, local model. No API key needed.",
            "speed": "slow (local)",
            "cost": "Free"
        },
        "llama-3.3-70b-versatile": {
            "name": "🟢 Llama 3.3-70b (Groq - API)",
            "provider": "groq",
            "model_id": "llama-3.3-70b-versatile",
            "description": "Faster online model. Requires Groq API key.",
            "speed": "fast (API)",
            "cost": "Pay per API call"
        }
    }
    
    def __init__(self):
        self.current_model = "gemma4:e2b"
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
    
    def get_model_info(self, model_id: str) -> dict:
        """Get full info for a model"""
        if model_id not in self.MODELS:
            return {}
        return self.MODELS[model_id].copy()
    
    def get_all_models(self) -> list:
        """Get list of (model_id, display_name) tuples"""
        return [(key, self.MODELS[key]["name"]) for key in self.MODELS.keys()]
    
    def set_current_model(self, model_id: str) -> bool:
        """Switch to a different model"""
        if model_id not in self.MODELS:
            return False
        
        # Check if Groq model and API key exists
        if model_id == "llama-3.3-70b-versatile" and not self.groq_api_key:
            return False
        
        self.current_model = model_id
        return True
    
    def get_current_model(self) -> str:
        """Get currently selected model ID"""
        return self.current_model
    
    def get_current_model_name(self) -> str:
        """Get human-readable name of current model"""
        return self.MODELS[self.current_model]["name"]
    
    def get_provider(self) -> str:
        """Get provider of current model"""
        return self.MODELS[self.current_model]["provider"]
    
    def is_groq(self) -> bool:
        """Check if current model is Groq"""
        return self.get_provider() == "groq"
    
    def is_ollama(self) -> bool:
        """Check if current model is Ollama"""
        return self.get_provider() == "ollama"
    
    def validate_groq_key(self) -> bool:
        """Validate Groq API key exists"""
        return bool(self.groq_api_key)


# Global instance
model_manager = ModelManager()

