"""
Simple Logger Integration for RAG Pipeline
Just drop this in your RAG pipeline to add logging!
"""

# At the top of your rag_pipeline.py, add:
# from logger_config import ExecutionLogger, PipelineStage
# 
# Then wrap your ask() function like this:

def ask_with_logging(question, conversation_history=None, session_id="session_1"):
    """
    RAG Pipeline with comprehensive logging
    
    Usage:
        result = ask_with_logging(question, conversation_history)
    """
    
    # Create logger
    logger = ExecutionLogger(question, session_id)
    
    try:
        # Log start of validation
        logger.log_stage_start(PipelineStage.INPUT_VALIDATION)
        logger.log_stage_success(PipelineStage.INPUT_VALIDATION, {"query_length": len(question)})
        
        # Log intent detection
        logger.log_stage_start(PipelineStage.INTENT_DETECTION)
        # ... your intent detection code ...
        logger.log_stage_success(PipelineStage.INTENT_DETECTION, {"intent": "admission"})
        
        # Log history
        logger.log_stage_start(PipelineStage.HISTORY_RETRIEVAL)
        logger.log_stage_success(PipelineStage.HISTORY_RETRIEVAL, {"history_available": True})
        
        # Log embedding
        logger.log_stage_start(PipelineStage.QUERY_EMBEDDING)
        # ... your embedding code ...
        logger.log_stage_success(PipelineStage.QUERY_EMBEDDING, {"vector_dim": 768})
        
        # Log Qdrant search
        logger.log_stage_start(PipelineStage.QDRANT_SEARCH)
        # ... your Qdrant search code ...
        logger.log_stage_success(PipelineStage.QDRANT_SEARCH, {"chunks_found": 5})
        
        # Log chunk retrieval
        logger.log_stage_start(PipelineStage.CHUNK_RETRIEVAL)
        # ... your retrieval code ...
        logger.log_stage_success(PipelineStage.CHUNK_RETRIEVAL, {"chunks": 5})
        
        # Log context building
        logger.log_stage_start(PipelineStage.CONTEXT_BUILDING)
        # ... your context code ...
        logger.log_stage_success(PipelineStage.CONTEXT_BUILDING, {"context_length": 5000})
        
        # Log prompt selection
        logger.log_stage_start(PipelineStage.PROMPT_SELECTION)
        # ... your prompt selection ...
        logger.log_stage_success(PipelineStage.PROMPT_SELECTION, {"prompt_type": "INFORMATION-FIRST"})
        
        # Log answer generation
        logger.log_stage_start(PipelineStage.ANSWER_GENERATION)
        result = ask(question, conversation_history)  # Call original ask()
        
        if result["answer"]:
            logger.log_final_answer(result["answer"], result.get("chunks", []))
            logger.log_stage_success(PipelineStage.ANSWER_GENERATION, 
                                    {"answer_length": len(result["answer"])})
        else:
            logger.log_no_answer("No answer generated")
            logger.log_stage_error(PipelineStage.ANSWER_GENERATION, Exception("Empty answer"))
        
        # Log completion
        logger.log_stage_start(PipelineStage.COMPLETION)
        logger.log_stage_success(PipelineStage.COMPLETION)
        
    except Exception as e:
        logger.log_stage_error(PipelineStage.ANSWER_GENERATION, e)
        result = {
            "answer": f"Error: {str(e)}",
            "chunks": [],
            "sources": []
        }
    
    finally:
        # Save log and print summary
        logger.save_execution_log()
        logger.print_summary()
    
    return result

# ════════════════════════════════════════════════════════════════════════════
# TO USE THIS:
# 1. In your Streamlit app, import: from rag_pipeline import ask_with_logging
# 2. Replace: result = ask(...) with result = ask_with_logging(...)
# 3. Make sure to pass session_id from st.session_state
# Example:
#    result = ask_with_logging(question, conversation_history, 
#                             session_id=st.session_state.session_id)
# ════════════════════════════════════════════════════════════════════════════
