from elasticsearch import AsyncElasticsearch
from app.core.config import settings

class ElasticsearchClient:
    def __init__(self, index_name):
        self.index_name = index_name
        self.client = AsyncElasticsearch(hosts=[f"http://{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"])
        self.mappings = {
            "properties": {
                "name": {"type": "text"},
                "description": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}}
                },
                "available_quantity": {"type": "integer"},
                "unit_price": {"type": "float"},
                "sku": {"type": "keyword"},
            }
        }

    async def _ensure_index(self):
        if not await self.client.indices.exists(index=self.index_name):
            await self.client.indices.create(index=self.index_name, mappings=self.mappings)

    async def crud_document(self, key, value: dict):
        if key == "inventory.created":
            await self.client.index(index=self.index_name, id=str(value["id"]), document=value)
        elif key == "inventory.updated":
            await self.client.update(index=self.index_name, id=str(value["id"]), document=value)
        elif key == "inventory.deleted":
            await self.client.delete(index=self.index_name, id=str(value["id"]))

    async def search_documents(self, query: str):
        "this method performs a compound query on the ES index"
        search_query: dict = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["name^3", "description"],
                                "fuzziness": "AUTO"
                            }
                        }
                    ],
                }
            }
        }
        response = await self.client.search(index=self.index_name, body=search_query)
        parsed_response = [
            {
                "id": hit["_id"],
                "name": hit["_source"]["name"],
                "description": hit["_source"]["description"],
                "available_quantity": hit["_source"]["available_quantity"],
                "unit_price": hit["_source"]["unit_price"],
                "sku": hit["_source"]["sku"]
            }
            for hit in response["hits"]["hits"]
        ]
        return parsed_response

elasticsearch_client = ElasticsearchClient(index_name="search_index")