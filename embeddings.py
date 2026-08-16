"""
Embedding Pipeline for BIT Jaipur RAG
Embeds chunks (from bit_jaipur_chunks.json) using Ollama EmbeddingGemma
and stores them in a NEW Qdrant collection, separate from the existing
"bitjaipur_master_context" collection.
"""

import json
import hashlib
from pathlib import Path
from tqdm import tqdm
import requests
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

try:
    import tiktoken
    _ENCODER = tiktoken.encoding_for_model("gpt-3.5-turbo")
except Exception:
    _ENCODER = None


class EmbeddingPipeline:
    def __init__(
        self,
        chunks_file=str(Path(__file__).parent / "data" / "bit_jaipur_chunks.json"),
        collection_name="bitjaipur_embedded_data",
        ollama_host="http://localhost:11434",
        embedding_model="embeddinggemma",
        qdrant_host="localhost",
        qdrant_port=6333
    ):
        """
        Initialize embedding pipeline

        Args:
            chunks_file: Path to bit_jaipur_chunks.json (JSON array, not JSONL)
            collection_name: NEW Qdrant collection name (kept separate from
                the existing "bitjaipur_master_context" collection so this
                run never overwrites your current data)
            ollama_host: Ollama API endpoint
            embedding_model: Model to use for embeddings
            qdrant_host: Qdrant server host
            qdrant_port: Qdrant server port
        """
        self.chunks_file = Path(chunks_file)
        self.collection_name = collection_name
        self.ollama_host = ollama_host
        self.embedding_model = embedding_model

        # Initialize Qdrant client
        self.qdrant = QdrantClient(host=qdrant_host, port=qdrant_port)

        self.stats = {
            "total_chunks": 0,
            "embedded": 0,
            "failed": 0,
            "embedding_dim": 0,
            "total_tokens_embedded": 0
        }

        print(f"\n📋 Configuration:")
        print(f"   Collection: {collection_name}")
        print(f"   Ollama: {ollama_host}")
        print(f"   Model: {embedding_model}")
        print(f"   Qdrant: {qdrant_host}:{qdrant_port}")

    def load_chunks(self):
        """Load chunks from the JSON array produced by chunk_data_tiktoken.py"""
        try:
            with open(self.chunks_file, 'r', encoding='utf-8') as f:
                chunks = json.load(f)
            return chunks
        except Exception as e:
            print(f"❌ Error loading chunks: {e}")
            return []

    def count_tokens(self, text):
        """Token count for stats/payload (falls back to word count if tiktoken unavailable)"""
        if _ENCODER is not None:
            return len(_ENCODER.encode(text))
        return len(text.split())

    def embed_text(self, text):
        """Embed text using Ollama"""
        try:
            response = requests.post(
                f"{self.ollama_host}/api/embeddings",
                json={
                    "model": self.embedding_model,
                    "prompt": text
                },
                timeout=60
            )

            if response.status_code == 200:
                embedding = response.json()["embedding"]
                return embedding
            else:
                print(f"❌ Ollama error: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Embedding error: {e}")
            return None

    def create_collection(self, vector_size):
        """Create Qdrant collection (fails loudly if it already exists with a
        different vector size, since this is meant to be a fresh collection)"""
        try:
            try:
                existing = self.qdrant.get_collection(self.collection_name)
                existing_size = existing.config.params.vectors.size
                if existing_size != vector_size:
                    print(
                        f"❌ Collection '{self.collection_name}' already exists "
                        f"with dim {existing_size}, but new embeddings are dim {vector_size}."
                    )
                    return False
                print(f"✅ Collection '{self.collection_name}' already exists (dim: {existing_size}) — will upsert into it")
                return True
            except Exception:
                # Collection doesn't exist yet -- create it
                self.qdrant.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE
                    )
                )
                print(f"✅ Created new collection '{self.collection_name}' (dim: {vector_size})")
                return True
        except Exception as e:
            print(f"❌ Error creating collection: {e}")
            return False

    def generate_point_id(self, chunk_id):
        """Generate unique Qdrant point ID from chunk ID"""
        hash_obj = hashlib.sha256(chunk_id.encode())
        return int(hash_obj.hexdigest(), 16) % (2**63)

    def run(self):
        """Execute embedding pipeline"""
        print(f"\n📂 Loading chunks from: {self.chunks_file.absolute()}")

        chunks = self.load_chunks()
        self.stats["total_chunks"] = len(chunks)

        if not chunks:
            print("❌ No chunks found!")
            return

        print(f"✅ Loaded {len(chunks)} chunks\n")

        # Embed first chunk to get dimension
        print("🔍 Detecting embedding dimension...")
        first_embedding = self.embed_text(chunks[0]["content"][:100])

        if not first_embedding:
            print("❌ Failed to get embedding")
            return

        embedding_dim = len(first_embedding)
        self.stats["embedding_dim"] = embedding_dim
        print(f"✅ Embedding dimension: {embedding_dim}\n")

        # Create collection
        print("📦 Setting up Qdrant collection...")
        if not self.create_collection(embedding_dim):
            return

        # Embed and upsert chunks
        print(f"\n🔄 Embedding and upserting {len(chunks)} chunks...\n")

        points = []

        for chunk in tqdm(chunks, desc="Embedding chunks"):
            # Get embedding
            embedding = self.embed_text(chunk["content"])

            if embedding is None:
                self.stats["failed"] += 1
                continue

            self.stats["embedded"] += 1
            token_count = self.count_tokens(chunk["content"])
            self.stats["total_tokens_embedded"] += token_count

            # Create point for Qdrant
            point_id = self.generate_point_id(chunk["chunk_id"])

            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "chunk_id": chunk["chunk_id"],
                    "file_name": chunk.get("file_name", ""),
                    "category": chunk.get("category", ""),
                    "chunk_index": chunk["chunk_index"],
                    "total_chunks": chunk.get("total_chunks", 0),
                    "content": chunk["content"],
                    "tokens": token_count,
                    "relative_path": chunk.get("relative_path", "")
                }
            )
            points.append(point)

        # Upsert all points to Qdrant (batched to avoid oversized requests)
        print(f"\n💾 Upserting {len(points)} points to Qdrant...")
        try:
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.qdrant.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
            print(f"✅ Successfully upserted {len(points)} points")
        except Exception as e:
            print(f"❌ Error upserting: {e}")
            return

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print embedding summary"""
        print("\n" + "=" * 70)
        print("✅ EMBEDDING COMPLETE")
        print("=" * 70)

        print(f"\n📊 Statistics:")
        print(f"   Total Chunks: {self.stats['total_chunks']}")
        print(f"   ✅ Embedded: {self.stats['embedded']}")
        print(f"   ❌ Failed: {self.stats['failed']}")

        print(f"\n📈 Embeddings:")
        print(f"   Dimension: {self.stats['embedding_dim']}")
        print(f"   Total Tokens: {self.stats['total_tokens_embedded']:,}")
        print(f"   Model: {self.embedding_model}")

        print(f"\n💾 Qdrant:")
        print(f"   Collection: {self.collection_name}")
        print(f"   Points Stored: {self.stats['embedded']}")

        print("\n" + "=" * 70)
        print("✨ Ready for RAG queries!")
        print("=" * 70 + "\n")


def main():
    """Run embedding pipeline"""
    pipeline = EmbeddingPipeline(
        collection_name="bit_jaipur_data",
        ollama_host="http://localhost:11434",
        embedding_model="embeddinggemma",
        qdrant_host="localhost",
        qdrant_port=6333
    )

    pipeline.run()


if __name__ == "__main__":
    main()