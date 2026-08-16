# 🎓 BIT Jaipur RAG Chatbot

A **Retrieval-Augmented Generation (RAG)** conversational AI assistant for **BIT Mesra, Jaipur Campus**. This chatbot answers questions about admissions, programs, faculty, placements, campus life, fees, scholarships, policies, and more — grounded strictly in the institution's official documents.

Built with a **dual-LLM architecture** (local + cloud), **Qdrant vector database**, **semantic chunking**, **smart intent detection**, and a **comprehensive benchmarking & logging suite**.

---

## ✨ Features

### 🤖 Dual-LLM Support
| Model | Provider | Speed | Cost | Requirement |
|-------|----------|-------|------|-------------|
| **Gemma 4 e2b** | Ollama (Local) | 10–15s | Free | Ollama installed locally |
| **Llama 3.3-70b-versatile** | Groq (API) | 2–5s | Pay per API call | `GROQ_API_KEY` in `.env` |

- **Dynamic model switching** at runtime from the Streamlit sidebar
- **Real-time token streaming** for both models
- Consistent `temperature=0.3` across both models for strict, grounded answers

### 🧠 Advanced RAG Pipeline
- **Semantic chunking** using `semantic-text-splitter` with tiktoken tokenization (gpt-3.5-turbo encoding)
- **768-dim embeddings** via Ollama's `embeddinggemma` model
- **Qdrant vector search** with cosine similarity (threshold ≥ 0.4)
- **Hybrid re-ranking**: vector similarity + filename-keyword overlap + role-term content matching
- **Page-marker-aware chunking** to keep section headings attached to their content
- **Known data corrections** override stale/conflicting source documents

### 🎯 Smart Intent Detection
Automatically classifies queries into:
- `admission` — applications, eligibility, fees, requirements
- `exploring` — campus, facilities, programs
- `undecided` — help deciding, comparisons
- `rejection` — not interested, other options
- `casual` — greetings, general chat

### 💬 Dual Prompt System
1. **Information-First** — for admission, exploring, undecided intents (strict, factual)
2. **Casual-Friendly** — for casual chat, rejection intents (friendly but strict)

### 🛡️ Safety & Guardrails
- **Foul language detection** — refuses vulgar content
- **Joke/roast detection** — refuses non-serious requests
- **Strict college-only scope** — refuses out-of-scope questions
- **Direct question handling** — answers personal eligibility questions directly
- **Program attribution** — never presents one program's numbers as general criteria

### 🧠 Smart Conversation Memory
- Remembers last **5 Q&A pairs**
- **Keyword-overlap matching** to decide when history is relevant
- Prevents hallucination by focusing on current topic

### 📊 Benchmarking & Evaluation Suite
- **64-question benchmark set** across 11 categories
- Automated metrics: retrieval success, keyword match, hallucination proxy, latency, confidence
- **Stratified sampling** for Groq (saves API quota)
- **Human-verified accuracy** workflow with `human_verified_correct` column
- **Visualization** of results by model and category

### 📝 Comprehensive Logging
- **Per-stage pipeline logging** (13 stages tracked)
- Execution logs, error logs, and daily summaries
- **Real-time log viewer** Streamlit app
- **User feedback** (👍/👎) with live session accuracy

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. DATA INGESTION & CURATION                                        │
│    BIT_Jaipur_Data/ (PDFs) → pdf_to_json.py → data/bit_jaipur_data.json │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. PROCESSING & CHUNKING                                            │
│    chunk_data.py → Semantic chunking (1000 tokens, 20% overlap)     │
│    → data/bit_jaipur_chunks.json                                    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. EMBEDDINGS                                                       │
│    embeddings.py → Ollama embeddinggemma → 768-dim vectors          │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. VECTOR DB                                                        │
│    Qdrant (localhost:6333) → collection: bit_jaipur_data            │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 5. CONTEXT RETRIEVAL (rag_pipeline_dual.py)                         │
│    User Query → Embed → Similarity Search → Top-K Context (5 chunks)│
│    + Keyword/role re-ranking                                         │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 6. DUAL-LLM GENERATION                                              │
│    Intent Detection → Prompt Selection → Gemma 4 e2b / Llama 3.3-70b│
│    → Grounded Response (temperature=0.3, max_tokens=5000)           │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 7. USER INTERFACE (Streamlit)                                       │
│    app.py / app_test.py → Chat UI with sources, confidence, feedback│
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
bit_jaipur_chatbot/
├── app.py                          # Main Streamlit chat UI
├── app_test.py                     # Enhanced UI (confidence meter, feedback)
├── app_architecture.py             # Architecture diagram (Graphviz)
├── rag_pipeline_dual.py            # ⭐ Core dual-LLM RAG pipeline
├── model_manager.py                # Runtime model switching
├── model_router_v2.py              # ⚠️ Deprecated (use rag_pipeline_dual.py)
├── pdf_to_json.py                  # PDF → JSON extraction
├── chunk_data.py                   # Semantic chunking
├── embeddings.py                   # Embedding pipeline → Qdrant
├── logger_config.py                # Comprehensive pipeline logger
├── logger_wrapper.py               # Logger wrapper for ask()
├── LOGGER_INTEGRATION_SIMPLE.py    # Simple logger integration example
├── log_viewer.py                   # Real-time log viewer UI
├── run_benchmark.py                # Benchmark runner
├── benchmark_questions.py          # 64-question benchmark set
├── analyze_results.py              # Benchmark results analysis
├── visualize_benchmark_summary.py  # Benchmark visualization
├── .env                            # LLM_CHOICE & GROQ_API_KEY
├── benchmark_results.csv           # Benchmark output (append-only)
├── feedback_log.csv                # User feedback log
├── benchmark_summary_plots/        # Generated benchmark charts
├── BIT_Jaipur_Data/                # Source PDFs (12 categories)
│   ├── 01_About_BIT_Jaipur/
│   ├── 02_Leadership_Administration/
│   ├── 03_Academics/
│   ├── 04_Students/
│   ├── 05_Admissions/
│   ├── 06_Departments/
│   ├── 07_Placements/
│   ├── 08_Fees_Scholarships/
│   ├── 09_Policies_Regulations/
│   ├── 10_Campus_Life/
│   ├── 11_FAQs/
│   └── 12_Sponsored_Research/
├── data/
│   ├── bit_jaipur_data.json        # Extracted PDF text
│   └── bit_jaipur_chunks.json      # Semantic chunks
└── logs/
    ├── rag_pipeline.log            # Simple logger output
    ├── executions/                 # Per-query execution logs
    ├── errors/                     # Error logs
    ├── summaries/                  # Daily summaries
    └── archive/                    # Archived logs
```

---

## 🚀 Getting Started

### Prerequisites

| Dependency | Version | Purpose |
|------------|---------|---------|
| Python | 3.9+ | Runtime |
| [Ollama](https://ollama.com/) | Latest | Local LLM + embeddings |
| [Qdrant](https://qdrant.tech/) | Latest | Vector database |
| Groq API key | — | For Llama 3.3-70b (optional) |

### 1. Install Dependencies

```bash
pip install streamlit qdrant-client requests python-dotenv pymupdf \
            semantic-text-splitter tiktoken tqdm groq \
            matplotlib seaborn pandas graphviz
```

### 2. Set Up Ollama Models

```bash
# Pull the LLM (Gemma 4 e2b)
ollama pull gemma4:e2b

# Pull the embedding model
ollama pull embeddinggemma
```

### 3. Configure Environment

Create a `.env` file in the project root:

```env
# LLM Configuration
# Options: ollama (default) or groq
LLM_CHOICE=ollama

# Groq API Key (required only if LLM_CHOICE=groq)
GROQ_API_KEY=your_groq_api_key_here
```

### 4. Start Services

```bash
# Start Ollama (if not already running)
ollama serve

# Start Qdrant (Docker)
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

### 5. Build the Knowledge Base (One-Time Setup)

```bash
# Step 1: Extract text from PDFs → data/bit_jaipur_data.json
python pdf_to_json.py

# Step 2: Semantic chunking → data/bit_jaipur_chunks.json
python chunk_data.py

# Step 3: Embed chunks → Qdrant collection "bit_jaipur_data"
python embeddings.py
```

### 6. Run the Chatbot

```bash
# Main chat UI
streamlit run app.py

# Enhanced UI (with confidence meter & feedback)
streamlit run app_test.py

# Architecture diagram
streamlit run app_architecture.py

# Log viewer
streamlit run log_viewer.py
```

---

## 💻 Usage

### Chat Interface

1. **Select a model** from the sidebar (Gemma 4 e2b or Llama 3.3-70b)
2. **Type a question** or click a sample question
3. View the answer with:
   - **Response time** (⚡/🚀/⭐/⏱️)
   - **Model used** (🟢 Gemma / 🔵 Llama)
   - **History used** (✅/❌)
   - **Prompt type** (📝 Information-First / 💬 Casual-Friendly)
   - **Sources** with relevance scores
   - **Full chunk content** from Qdrant
   - **Retrieval confidence meter** (app_test.py)
   - **👍/👎 feedback buttons** (app_test.py)

### Example Questions

| Category | Example |
|----------|---------|
| About | "When was BIT Mesra established?" |
| Leadership | "Who is the Director of BIT Jaipur?" |
| Academics | "What undergraduate programmes does BIT Jaipur offer?" |
| Admissions | "What is the minimum eligibility for BTech admission?" |
| Faculty | "Who is the HOD of CSE department?" |
| Fees | "What is the fee structure for BTech CSE?" |
| Placements | "What is the placement process at BIT Jaipur?" |
| Campus Life | "How big is the BIT Jaipur campus?" |
| Policies | "Does BIT Jaipur have an anti-ragging policy?" |
| FAQs | "What is the official website of BIT Mesra?" |

---

## 📊 Benchmarking

### Run the Benchmark

```bash
# Default: Gemma full set (64), Llama stratified sample (12)
python run_benchmark.py

# Change Groq sample size
python run_benchmark.py --groq-sample-size 15

# Only Gemma (full set)
python run_benchmark.py --model ollama

# Only Llama (sampled)
python run_benchmark.py --model groq

# Only Llama (ALL questions — burns more quota)
python run_benchmark.py --model groq --full-groq

# Quick smoke test (first 10 questions)
python run_benchmark.py --limit 10
```

### Metrics Tracked

| Metric | Description |
|--------|-------------|
| `retrieval_success` | Did the expected source document get retrieved? |
| `keyword_match` | Does the answer contain expected keywords? (proxy for correctness) |
| `hallucination_flag` | Automated proxy for ungrounded claims |
| `latency_seconds` | Wall-clock time for `ask()` to return |
| `confidence_label/pct` | Average retrieval similarity score |
| `top_sources` | Actual filenames retrieved |

### Analyze Results

```bash
# After filling in human_verified_correct in benchmark_results.csv
python analyze_results.py
```

### Visualize Results

```bash
python visualize_benchmark_summary.py
```

Charts are saved to `benchmark_summary_plots/`:
- `avg_confidence_by_category.png`
- `avg_confidence_by_model.png`
- `avg_latency_by_category.png`
- `avg_latency_by_model.png`
- `hallucination_rate_by_category.png`
- `hallucination_rate_by_model.png`
- `keyword_match_by_category.png`
- `keyword_match_by_model.png`
- `retrieval_success_by_category.png`
- `retrieval_success_by_model.png`

---

## 📝 Logging System

### Log Structure

```
logs/
├── rag_pipeline.log              # Simple file logger
├── executions/                   # Per-query JSON logs
│   └── {session}_{timestamp}_execution.json
├── errors/                       # Error-specific logs
│   └── {session}_{timestamp}_error.json
├── summaries/                    # Daily summary (JSONL)
│   └── daily_summary.jsonl
└── archive/                      # Archived logs
```

### Pipeline Stages Tracked

1. Input Validation
2. Safety Check (Foul Language)
3. Intent Detection
4. History Retrieval
5. Keyword Matching
6. Query Embedding (EmbeddingGemma)
7. Qdrant Vector Search
8. Chunk Retrieval
9. Context Building
10. Prompt Type Selection
11. Answer Generation
12. Response Assembly
13. Completion

### View Logs

```bash
streamlit run log_viewer.py
```

Features:
- **Execution Summary** — latest run details
- **Recent Executions** — last 20 runs
- **Error Logs** — error details with stage breakdown
- **Statistics** — success rate, avg duration, answer rate

---

## 🔧 Configuration

### Environment Variables (`.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_CHOICE` | `ollama` | `ollama` or `groq` |
| `GROQ_API_KEY` | — | Required for Groq model |

### Pipeline Constants (`rag_pipeline_dual.py`)

| Constant | Value | Description |
|----------|-------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama API endpoint |
| `QDRANT_HOST` | `localhost` | Qdrant host |
| `QDRANT_PORT` | `6333` | Qdrant port |
| `COLLECTION_NAME` | `bit_jaipur_data` | Qdrant collection |
| `EMBEDDING_MODEL` | `embeddinggemma` | Embedding model |
| `SIMILARITY_THRESHOLD` | `0.4` | Minimum relevance score |
| `MAX_CONVERSATION_HISTORY` | `5` | Q&A pairs remembered |
| `MAX_TOKENS_GENERATION` | `5000` | Max output tokens |
| `REQUEST_TIMEOUT` | `600` | API timeout (seconds) |

### Chunking Parameters (`chunk_data.py`)

| Parameter | Value | Description |
|-----------|-------|-------------|
| `TOKENIZER_MODEL` | `gpt-3.5-turbo` | Tokenizer for sizing |
| `MAX_TOKENS` | `1000` | Max tokens per chunk |
| `OVERLAP_RATIO` | `0.20` | Overlap between chunks |
| `MIN_CHUNK_WORDS` | `10` | Merge chunks below this |
| `SECTION_MAX_TOKEN_MULTIPLIER` | `1.5` | Max section size before subdividing |

---

## 🧪 Testing

### Benchmark Questions

```bash
# View question set summary
python benchmark_questions.py
```

The 64-question set covers 11 categories:
- about (7), academics (4), admissions (11), behavioral (6), campus_life (7), faculty (16), faqs (4), fees (7), placements (7), policies (4), student_life (3)

### Known Data Conflicts

The pipeline includes a `KNOWN_DATA_CORRECTIONS` override for the CSE HOD conflict:
- **Correct**: Dr. Shripal Vijayvargiya (per CSE department documents)
- **Stale**: Dr. Madhavi Sinha (per Contact_Details_Incharges.pdf)

---

## 🛠️ Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **Ollama not running** | Run `ollama serve` |
| **Qdrant not running** | `docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant` |
| **Model not found** | `ollama pull gemma4:e2b` and `ollama pull embeddinggemma` |
| **Groq API key missing** | Add `GROQ_API_KEY` to `.env` |
| **Empty answers** | Check Qdrant collection exists: `python embeddings.py` |
| **Slow responses** | Use Groq model (Llama 3.3-70b) for faster answers |
| **Streaming errors** | Falls back to non-streaming mode automatically |

### Model Switching

The `LLM_CHOICE` environment variable controls which model is used:
- `ollama` → Gemma 4 e2b (local, free)
- `groq` → Llama 3.3-70b-versatile (API, faster)

The Streamlit UI updates this at runtime via `model_manager.py`.

---

## 📄 License

This project is for educational and informational purposes. All institutional data belongs to BIT Mesra, Jaipur Campus.

---

## 🙏 Acknowledgments

- **BIT Mesra, Jaipur Campus** — for providing the institutional data
- **Ollama** — for local LLM and embedding models
- **Groq** — for fast cloud LLM inference
- **Qdrant** — for vector database
- **Streamlit** — for the web UI framework

---

*Built with ❤️ for BIT Mesra Jaipur | Powered by Gemma 4 e2b + Llama 3.3-70b + Advanced RAG + Real-time Streaming*