from elasticsearch import AsyncElasticsearch
from app.core.config import settings

class ElasticsearchClient:
    """this is the encapsulation of the logics that are involved in the Elastic Search CRUD operations performed on the inventory events/messages"""
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
                "quantity": {"type": "integer"},
                "price": {"type": "float"},
                "sku": {"type": "keyword"},
            }
        }

    async def _ensure_index(self):
        "Checks if the index is created, if it isn't, it is created"
        if not await self.client.indices.exists(index=self.index_name):
            await self.client.indices.create(index=self.index_name, mappings=self.mappings)

    async def crud_document(self, key, value: dict):
        "this method does CUD ops on the message gotten from the inventory kafka topic"
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
        return response

elasticsearch_client = ElasticsearchClient(index_name="search_index")