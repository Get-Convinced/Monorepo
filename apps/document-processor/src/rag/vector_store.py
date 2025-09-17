"""
Vector store interface for QDrant operations.
"""

import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

logger = logging.getLogger(__name__)


class VectorStore:
    """Vector store interface for QDrant operations."""
    
    def __init__(self, qdrant_url: str = "http://localhost:6336"):
        self.client = QdrantClient(url=qdrant_url)
    
    async def ensure_collection_exists(
        self, 
        collection_name: str, 
        vector_size: int = 1024,
        distance: Distance = Distance.COSINE
    ) -> bool:
        """Ensure collection exists with proper configuration."""
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=distance)
                )
                logger.info(f"Created collection: {collection_name} with dimension {vector_size}")
                return True
            else:
                logger.info(f"Collection {collection_name} already exists")
                return False
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
            raise
    
    async def upsert_points(self, collection_name: str, points: List[Dict[str, Any]]) -> bool:
        """Upsert points into collection."""
        try:
            # Ensure collection exists
            await self.ensure_collection_exists(collection_name)
            
            # Convert dict points to PointStruct
            point_structs = []
            for point in points:
                point_structs.append(PointStruct(
                    id=point["id"],
                    vector=point["vector"],
                    payload=point["payload"]
                ))
            
            # Upsert points
            self.client.upsert(
                collection_name=collection_name,
                points=point_structs
            )
            
            logger.info(f"Upserted {len(points)} points into collection {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error upserting points: {e}")
            raise
    
    async def search(
        self, 
        collection_name: str, 
        query_vector: List[float], 
        limit: int = 5,
        score_threshold: float = 0.7,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        try:
            # Build filter if provided
            search_filter = None
            if filter_conditions:
                conditions = []
                for field, value in filter_conditions.items():
                    conditions.append(
                        FieldCondition(
                            key=field,
                            match=MatchValue(value=value)
                        )
                    )
                search_filter = Filter(must=conditions)
            
            # Search
            search_results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=search_filter
            )
            
            # Format results
            results = []
            for result in search_results:
                results.append({
                    "id": result.id,
                    "score": float(result.score),
                    "payload": result.payload
                })
            
            logger.info(f"Found {len(results)} results for search in {collection_name}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching vectors: {e}")
            raise
    
    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get collection information."""
        try:
            info = self.client.get_collection(collection_name)
            return {
                "name": info.config.params.vectors.size,
                "vector_size": info.config.params.vectors.size,
                "distance": info.config.params.vectors.distance,
                "points_count": info.points_count,
                "status": info.status
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            raise
    
    async def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection."""
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            raise
    
    async def list_collections(self) -> List[str]:
        """List all collections."""
        try:
            collections = self.client.get_collections()
            return [col.name for col in collections.collections]
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            raise
