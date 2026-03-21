import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

load_dotenv()

# Config
QDRANT_URL = f"http://{os.getenv('QDRANT_HOST', 'localhost')}:6333"
COLLECTION_NAME = "harshgpt"

# Init
client = QdrantClient(url=QDRANT_URL)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Vector Store
vectorstore = QdrantVectorStore(
    client=client,
    collection_name=COLLECTION_NAME,
    embedding=embeddings,
    content_payload_key="text",  
    metadata_payload_key="metadata"
)

BASE_SEARCH_KWARGS = {
    "k": 3,
    "fetch_k": 20, # feticing 15 showing top 3
    "lambda_mult": 0.5 # 50% relevance ad 50 % diversity
}

# Default retriever (no filter) - MMR across all PDFs
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs=BASE_SEARCH_KWARGS
)

def retrieve_chunks(query: str, source_filter: str = None):

    if source_filter:
        # Similarity search for filtered (small subset)
        retriever_to_use = vectorstore.as_retriever(
            search_type="similarity",   # 👈 similarity not MMR
            search_kwargs={
                "k": 5,                 # 👈 get more chunks from filtered source
                "filter": Filter(
                    must=[
                        FieldCondition(
                            key="metadata.source",
                            match=MatchValue(value=source_filter)
                        )
                    ]
                )
            }
        )
    else:
        retriever_to_use = retriever

    chunks = retriever_to_use.invoke(query)

    if not chunks:
        print(f"No relevant chunks found for: {query}")
        return []

    return chunks

