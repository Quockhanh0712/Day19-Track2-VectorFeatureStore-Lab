import time
from typing import List

from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from feast import FeatureStore

class HybridMemoryAgent:
    def __init__(self, feast_repo_path: str):
        # 1. Init Vector Store (Qdrant in-memory for POC)
        self.qdrant = QdrantClient(":memory:")
        self.qdrant.create_collection(
            collection_name="episodic_memory",
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
        self.embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        
        # 2. Init Feature Store
        self.fs = FeatureStore(repo_path=feast_repo_path)
        self._memory_counter = 0

    def remember(self, text: str, user_id: str = "u_001") -> None:
        """Add a new piece of episodic memory for this user."""
        # Embed text
        vector = list(self.embedder.embed([text]))[0].tolist()
        
        # Upsert into Qdrant
        self.qdrant.upsert(
            collection_name="episodic_memory",
            points=[
                PointStruct(
                    id=self._memory_counter,
                    vector=vector,
                    payload={"user_id": user_id, "text": text, "timestamp": time.time()}
                )
            ]
        )
        self._memory_counter += 1

    def recall(self, query: str, user_id: str = "u_001") -> str:
        """Retrieve top-K memories + user profile features -> return assembled context."""
        # 1. Lấy user profile + recent activity từ Feast online store
        # Xử lý trường hợp Exception nếu online store chưa có dữ liệu (do chưa materialize)
        try:
            feature_vector = self.fs.get_online_features(
                features=[
                    "user_profile_features:reading_speed_wpm",
                    "user_profile_features:topic_affinity",
                    "query_velocity_features:queries_last_hour",
                ],
                entity_rows=[{"user_id": user_id}],
            ).to_dict()
            reading_speed = feature_vector.get("reading_speed_wpm", [None])[0]
            topic_affinity = feature_vector.get("topic_affinity", [None])[0]
            queries_last_hour = feature_vector.get("queries_last_hour", [None])[0]
        except Exception:
            # Fallback values nếu chưa chạy feast materialize
            reading_speed = 200
            topic_affinity = "unknown"
            queries_last_hour = 0
            
        # 2. Semantic search Qdrant filtered by user_id
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        q_vec = list(self.embedder.embed([query]))[0].tolist()
        hits = self.qdrant.query_points(
            collection_name="episodic_memory",
            query=q_vec,
            query_filter=Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
            ),
            limit=3
        ).points
        
        top_memories = [h.payload["text"] for h in hits]
        
        # 3. Assemble context string
        context = (
            f"User likes <{topic_affinity}> reading at <{reading_speed}> wpm.\n"
            f"Recent activity: <{queries_last_hour}> queries in the last hour.\n"
            f"Top memories:\n"
        )
        for i, mem in enumerate(top_memories, 1):
            context += f"  {i}. {mem}\n"
            
        return context
