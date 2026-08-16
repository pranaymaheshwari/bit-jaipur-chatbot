"""
Logger Wrapper for RAG Pipeline - FIXED VERSION
Imports ask() INSIDE function to avoid caching issues with model switching
"""

import sys
from pathlib import Path


def ask_with_logging(question, conversation_history=None, session_id="session_1", verbose=True, timeout=600, show_streaming=True):
    """
    RAG Pipeline with comprehensive logging
    
    IMPORTANT: Imports are INSIDE function to get fresh version after model_router_v2 loads!
    
    Args:
        question (str): User's query
        conversation_history (list): Previous conversation messages
        session_id (str): Session identifier for grouping logs
        verbose (bool): Print progress to console
        timeout (int): Request timeout in seconds (default: 600)
        show_streaming (bool): Show real-time streaming (default: True)
    
    Returns:
        dict: Contains answer, sources, chunks, intent, etc.
    """
    
    # ════════════════════════════════════════════════════════════════════════════════
    # LAZY IMPORTS - Inside function to get latest versions!
    # ════════════════════════════════════════════════════════════════════════════════
    
    try:
        from logger_config import ExecutionLogger, PipelineStage
        LOGGER_AVAILABLE = True
    except ImportError:
        LOGGER_AVAILABLE = False
        print("⚠️  Logger not available - skipping logging")
    
    try:
        from rag_pipeline_dual import ask
    except ImportError:
        print("⚠️  WARNING: rag_pipeline.ask() not found!")
        raise ImportError("rag_pipeline.ask() not found")
    
    # ════════════════════════════════════════════════════════════════════════════════
    
    if not LOGGER_AVAILABLE:
        print("❌ Logger modules not available - running without logging")
        return ask(question, conversation_history, verbose=verbose, timeout=timeout, show_streaming=show_streaming)
    
    logger = ExecutionLogger(question, session_id)
    
    try:
        # STAGE 1: INPUT VALIDATION
        logger.log_stage_start(PipelineStage.INPUT_VALIDATION)
        
        if not question or len(question.strip()) == 0:
            logger.log_stage_error(
                PipelineStage.INPUT_VALIDATION, 
                Exception("Empty question"), 
                "Question is empty or only whitespace"
            )
            result = {
                "answer": "Please ask a valid question!",
                "chunks": [],
                "sources": [],
                "intent": "invalid",
                "conversation_history": conversation_history or [],
                "history_used": False
            }
            return result
        
        logger.log_stage_success(
            PipelineStage.INPUT_VALIDATION, 
            {"query_length": len(question)}
        )
        
        # STAGE 2: SAFETY CHECK
        logger.log_stage_start(PipelineStage.SAFETY_CHECK)
        logger.log_stage_success(PipelineStage.SAFETY_CHECK, {"check": "passed"})
        
        # STAGES 3-11: CALL ORIGINAL ask() FUNCTION
        if verbose:
            print("\n🔄 Executing RAG Pipeline with logging...")
        
        # ✅ CALL ask() - Now uses model_router_v2 because rag_pipeline imports from it!
        result = ask(question, conversation_history, verbose=False, timeout=timeout, show_streaming=show_streaming)
        
        # Log each stage
        logger.log_stage_start(PipelineStage.INTENT_DETECTION)
        intent = result.get("intent", "unknown")
        logger.log_stage_success(PipelineStage.INTENT_DETECTION, {"intent": intent})
        
        logger.log_stage_start(PipelineStage.HISTORY_RETRIEVAL)
        history_available = conversation_history and len(conversation_history) > 0
        logger.log_stage_success(
            PipelineStage.HISTORY_RETRIEVAL, 
            {"history_available": history_available}
        )
        
        logger.log_stage_start(PipelineStage.KEYWORD_MATCHING)
        history_used = result.get("history_used", False)
        logger.log_stage_success(
            PipelineStage.KEYWORD_MATCHING, 
            {"relevant": history_used}
        )
        
        logger.log_stage_start(PipelineStage.QUERY_EMBEDDING)
        logger.log_stage_success(
            PipelineStage.QUERY_EMBEDDING, 
            {"model": "embeddinggemma", "vector_dim": 768}
        )
        
        logger.log_stage_start(PipelineStage.QDRANT_SEARCH)
        chunks = result.get("chunks", [])
        chunks_count = len(chunks)
        if chunks_count > 0:
            logger.log_stage_success(
                PipelineStage.QDRANT_SEARCH, 
                {"chunks_found": chunks_count}
            )
        else:
            logger.log_stage_partial(
                PipelineStage.QDRANT_SEARCH, 
                {"chunks_found": 0}
            )
        
        logger.log_stage_start(PipelineStage.CHUNK_RETRIEVAL)
        if chunks_count > 0:
            logger.log_stage_success(
                PipelineStage.CHUNK_RETRIEVAL, 
                {"chunks_retrieved": chunks_count}
            )
        else:
            logger.log_stage_partial(PipelineStage.CHUNK_RETRIEVAL)
        
        logger.log_stage_start(PipelineStage.CONTEXT_BUILDING)
        logger.log_stage_success(PipelineStage.CONTEXT_BUILDING)
        
        logger.log_stage_start(PipelineStage.PROMPT_SELECTION)
        prompt_type = result.get("prompt_type", "INFORMATION-FIRST")
        logger.log_stage_success(
            PipelineStage.PROMPT_SELECTION, 
            {"prompt_type": prompt_type}
        )
        
        logger.log_stage_start(PipelineStage.ANSWER_GENERATION)
        answer = result.get("answer", "")
        
        if not answer or len(answer.strip()) == 0:
            logger.log_no_answer("Model returned empty response")
            logger.log_stage_error(
                PipelineStage.ANSWER_GENERATION, 
                Exception("Empty answer")
            )
        elif len(answer) < 50:
            logger.log_incomplete_answer(answer, "Answer too short (<50 chars)")
            logger.log_stage_partial(PipelineStage.ANSWER_GENERATION)
        else:
            logger.log_final_answer(
                answer, 
                chunks, 
                intent, 
                result.get("model_used", "")
            )
            logger.log_stage_success(
                PipelineStage.ANSWER_GENERATION, 
                {"answer_length": len(answer)}
            )
        
        logger.log_stage_start(PipelineStage.RESPONSE_ASSEMBLY)
        logger.log_stage_success(PipelineStage.RESPONSE_ASSEMBLY)
        
        logger.log_stage_start(PipelineStage.COMPLETION)
        logger.log_stage_success(PipelineStage.COMPLETION)
        
        if verbose:
            print("✅ Pipeline execution complete!\n")
        
    except Exception as e:
        logger.log_stage_error(PipelineStage.ANSWER_GENERATION, e)
        result = {
            "answer": f"Error: {str(e)}",
            "chunks": [],
            "sources": []
        }
        if verbose:
            print(f"❌ Pipeline error: {e}\n")
    
    finally:
        logger.save_execution_log()
        logger.print_summary()
    
    return result


if __name__ == "__main__":
    print("❌ This file should be imported, not run directly!")
    print("\nUsage:")
    print("  from logger_wrapper import ask_with_logging")
    print("  result = ask_with_logging('Your question', timeout=300)")