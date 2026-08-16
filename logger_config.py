"""
BIT Jaipur RAG Chatbot - Comprehensive Data Logger
Tracks every stage of the RAG pipeline with timestamps and status
"""

import logging
import json
import os
from datetime import datetime
from pathlib import Path
from enum import Enum
from typing import Any, Dict, Optional

# ══════════════════════════════════════════════════════════════════════════════════
# CONSTANTS & ENUMS
# ══════════════════════════════════════════════════════════════════════════════════

class ExecutionStatus(Enum):
    """Status of each pipeline stage"""
    PENDING = "⏳ PENDING"
    IN_PROGRESS = "🔄 IN_PROGRESS"
    SUCCESS = "✅ SUCCESS"
    PARTIAL = "⚠️ PARTIAL"
    FAILED = "❌ FAILED"
    SKIPPED = "⊘ SKIPPED"


class PipelineStage(Enum):
    """RAG Pipeline stages"""
    INPUT_VALIDATION = "Input Validation"
    SAFETY_CHECK = "Safety Check (Foul Language)"
    INTENT_DETECTION = "Intent Detection"
    HISTORY_RETRIEVAL = "History Retrieval"
    KEYWORD_MATCHING = "Keyword Matching"
    QUERY_EMBEDDING = "Query Embedding (EmbeddingGemma)"
    QDRANT_SEARCH = "Qdrant Vector Search"
    CHUNK_RETRIEVAL = "Chunk Retrieval"
    CONTEXT_BUILDING = "Context Building"
    PROMPT_SELECTION = "Prompt Type Selection"
    ANSWER_GENERATION = "Answer Generation (Gemma 4 e2b)"
    RESPONSE_ASSEMBLY = "Response Assembly"
    COMPLETION = "Completion"


# ══════════════════════════════════════════════════════════════════════════════════
# DIRECTORIES
# ══════════════════════════════════════════════════════════════════════════════════

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

EXECUTION_LOG_DIR = LOG_DIR / "executions"
EXECUTION_LOG_DIR.mkdir(exist_ok=True)

ERROR_LOG_DIR = LOG_DIR / "errors"
ERROR_LOG_DIR.mkdir(exist_ok=True)

SUMMARY_LOG_DIR = LOG_DIR / "summaries"
SUMMARY_LOG_DIR.mkdir(exist_ok=True)

ARCHIVE_DIR = LOG_DIR / "archive"
ARCHIVE_DIR.mkdir(exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════════
# EXECUTION LOGGER CLASS
# ══════════════════════════════════════════════════════════════════════════════════

class ExecutionLogger:
    """Tracks complete execution of a single query through RAG pipeline"""
    
    def __init__(self, query: str, session_id: str):
        """
        Initialize logger for a query execution
        
        Args:
            query: User's input query
            session_id: Unique session identifier
        """
        self.query = query
        self.session_id = session_id
        self.execution_id = f"{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"
        self.start_time = datetime.now()
        
        # Track all stages
        self.stages: Dict[str, Dict[str, Any]] = {}
        self.current_stage: Optional[str] = None
        self.final_answer: Optional[str] = None
        self.error_message: Optional[str] = None
        self.error_stage: Optional[str] = None
        
        # Metadata
        self.metadata = {
            "execution_id": self.execution_id,
            "session_id": self.session_id,
            "query": query,
            "start_time": self.start_time.isoformat()
        }
    
    def log_stage_start(self, stage: PipelineStage, metadata: Optional[Dict] = None):
        """Log the start of a pipeline stage"""
        stage_name = stage.value
        self.current_stage = stage_name
        
        self.stages[stage_name] = {
            "stage": stage_name,
            "status": ExecutionStatus.IN_PROGRESS.value,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "duration_ms": None,
            "metadata": metadata or {},
            "result": None,
            "error": None
        }
        
        print(f"\n{ExecutionStatus.IN_PROGRESS.value} {stage_name}")
    
    def log_stage_success(self, stage: PipelineStage, result: Any = None, metadata: Optional[Dict] = None):
        """Log successful completion of a stage"""
        stage_name = stage.value
        
        if stage_name in self.stages:
            end_time = datetime.now()
            start_time = datetime.fromisoformat(self.stages[stage_name]["start_time"])
            duration = (end_time - start_time).total_seconds() * 1000
            
            self.stages[stage_name]["status"] = ExecutionStatus.SUCCESS.value
            self.stages[stage_name]["end_time"] = end_time.isoformat()
            self.stages[stage_name]["duration_ms"] = f"{duration:.2f}"
            self.stages[stage_name]["result"] = str(result)[:500] if result else None
            
            if metadata:
                self.stages[stage_name]["metadata"].update(metadata)
            
            print(f"{ExecutionStatus.SUCCESS.value} {stage_name} ({duration:.0f}ms)")
    
    def log_stage_partial(self, stage: PipelineStage, result: Any = None, metadata: Optional[Dict] = None):
        """Log partial completion of a stage (some data but incomplete)"""
        stage_name = stage.value
        
        if stage_name in self.stages:
            end_time = datetime.now()
            start_time = datetime.fromisoformat(self.stages[stage_name]["start_time"])
            duration = (end_time - start_time).total_seconds() * 1000
            
            self.stages[stage_name]["status"] = ExecutionStatus.PARTIAL.value
            self.stages[stage_name]["end_time"] = end_time.isoformat()
            self.stages[stage_name]["duration_ms"] = f"{duration:.2f}"
            self.stages[stage_name]["result"] = str(result)[:500] if result else None
            
            if metadata:
                self.stages[stage_name]["metadata"].update(metadata)
            
            print(f"{ExecutionStatus.PARTIAL.value} {stage_name} (Partial success)")
    
    def log_stage_error(self, stage: PipelineStage, error: Exception, error_msg: str = ""):
        """Log error in a stage"""
        stage_name = stage.value
        self.error_stage = stage_name
        self.error_message = str(error) if not error_msg else error_msg
        
        if stage_name in self.stages:
            end_time = datetime.now()
            start_time = datetime.fromisoformat(self.stages[stage_name]["start_time"])
            duration = (end_time - start_time).total_seconds() * 1000
            
            self.stages[stage_name]["status"] = ExecutionStatus.FAILED.value
            self.stages[stage_name]["end_time"] = end_time.isoformat()
            self.stages[stage_name]["duration_ms"] = f"{duration:.2f}"
            self.stages[stage_name]["error"] = {
                "type": type(error).__name__,
                "message": str(error),
                "custom_message": error_msg
            }
            
            print(f"{ExecutionStatus.FAILED.value} {stage_name}")
            print(f"   Error: {self.error_message}")
    
    def log_stage_skipped(self, stage: PipelineStage, reason: str = ""):
        """Log a skipped stage"""
        stage_name = stage.value
        
        self.stages[stage_name] = {
            "stage": stage_name,
            "status": ExecutionStatus.SKIPPED.value,
            "reason": reason,
            "start_time": datetime.now().isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration_ms": "0"
        }
        
        print(f"{ExecutionStatus.SKIPPED.value} {stage_name} - {reason}")
    
    def log_final_answer(self, answer: str, chunks: list = None, intent: str = "", model: str = ""):
        """Log the final answer and metadata"""
        self.final_answer = answer
        self.metadata.update({
            "answer_length": len(answer),
            "chunks_retrieved": len(chunks) if chunks else 0,
            "intent": intent,
            "model": model,
            "completed": True
        })
        
        print(f"\n✅ FINAL ANSWER: {len(answer)} characters")
        if chunks:
            print(f"   Chunks used: {len(chunks)}")
    
    def log_incomplete_answer(self, answer: str, reason: str = ""):
        """Log when answer was incomplete or partially generated"""
        self.final_answer = answer
        self.metadata.update({
            "answer_length": len(answer),
            "completed": False,
            "incompleteness_reason": reason
        })
        
        print(f"\n⚠️ INCOMPLETE ANSWER: {len(answer)} characters")
        print(f"   Reason: {reason}")
    
    def log_no_answer(self, reason: str = ""):
        """Log when no answer was generated at all"""
        self.final_answer = None
        self.metadata.update({
            "answer_generated": False,
            "reason": reason
        })
        
        print(f"\n❌ NO ANSWER GENERATED")
        print(f"   Reason: {reason}")
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of entire execution"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Count stages by status
        status_counts = {}
        for stage_info in self.stages.values():
            status = stage_info.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "execution_id": self.execution_id,
            "session_id": self.session_id,
            "query": self.query,
            "total_duration_seconds": f"{total_duration:.2f}",
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_stages": len(self.stages),
            "status_counts": status_counts,
            "error_stage": self.error_stage,
            "error_message": self.error_message,
            "answer_generated": self.final_answer is not None,
            "answer_length": len(self.final_answer) if self.final_answer else 0,
            "completed_successfully": self.error_stage is None
        }
    
    def save_execution_log(self):
        """Save execution log to JSON file"""
        summary = self.get_execution_summary()
        
        log_data = {
            "summary": summary,
            "stages": self.stages,
            "metadata": self.metadata,
            "final_answer": self.final_answer[:500] if self.final_answer else None  # First 500 chars
        }
        
        # Save detailed execution log
        execution_file = EXECUTION_LOG_DIR / f"{self.execution_id}_execution.json"
        with open(execution_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        # Save to summary log
        self._save_to_summary_log(summary)
        
        # Save error log if there was an error
        if self.error_stage:
            self._save_to_error_log(log_data)
        
        print(f"\n📁 Execution log saved: {execution_file}")
        return execution_file
    
    def _save_to_summary_log(self, summary: Dict):
        """Append to summary log file"""
        summary_file = SUMMARY_LOG_DIR / "daily_summary.jsonl"
        
        with open(summary_file, 'a') as f:
            f.write(json.dumps(summary) + '\n')
    
    def _save_to_error_log(self, log_data: Dict):
        """Save error log"""
        error_file = ERROR_LOG_DIR / f"{self.execution_id}_error.json"
        
        with open(error_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        print(f"⚠️ Error log saved: {error_file}")
    
    def print_summary(self):
        """Print execution summary to console"""
        summary = self.get_execution_summary()
        
        print("\n" + "="*80)
        print("EXECUTION SUMMARY")
        print("="*80)
        print(f"Execution ID: {summary['execution_id']}")
        print(f"Query: {summary['query'][:60]}...")
        print(f"Total Duration: {summary['total_duration_seconds']}s")
        print(f"Completed Successfully: {'✅ YES' if summary['completed_successfully'] else '❌ NO'}")
        
        if summary['error_stage']:
            print(f"Error Stage: {summary['error_stage']}")
            print(f"Error: {summary['error_message']}")
        
        print(f"\nStage Breakdown:")
        for status, count in summary['status_counts'].items():
            print(f"  {status}: {count}")
        
        print(f"\nAnswer Status:")
        print(f"  Generated: {'✅ YES' if summary['answer_generated'] else '❌ NO'}")
        if summary['answer_generated']:
            print(f"  Length: {summary['answer_length']} characters")
        
        print("="*80 + "\n")


# ══════════════════════════════════════════════════════════════════════════════════
# SIMPLE LOGGING SETUP
# ══════════════════════════════════════════════════════════════════════════════════

def setup_simple_logger(name: str) -> logging.Logger:
    """Setup a simple file-based logger"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # File handler
    log_file = LOG_DIR / f"{name}.log"
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    
    logger.addHandler(fh)
    
    return logger


# Create main logger
rag_logger = setup_simple_logger("rag_pipeline")

