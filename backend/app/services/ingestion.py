import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
# import uuid
import hashlib

load_dotenv()

# Config
QDRANT_URL = f"http://{os.getenv('QDRANT_HOST', 'localhost')}:6333"
COLLECTION_NAME = "harshgpt"
PDF_DIR = os.path.join(os.path.dirname(__file__), "../../database")

# Init
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
client = QdrantClient(url=QDRANT_URL)

def load_and_chunk_pdfs():
    all_chunks = []
    
    for filename in os.listdir(PDF_DIR):
        if filename.endswith(".pdf"):
            filepath = os.path.join(PDF_DIR, filename)
            print(f"Loading: {filename}")
            
            loader = PDFPlumberLoader(filepath)
            pages = loader.load()
            
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
            )
            chunks = splitter.split_documents(pages)
            
            # Add metadata
            for chunk in chunks:
                chunk.metadata["source"] = filename
                chunk.metadata["page"] = chunk.metadata.get("page", 0)#Take the page number from metadata if it exists, otherwise use 0
            
            all_chunks.extend(chunks)
            print(f"  → {len(chunks)} chunks from {filename}")
    
    print(f"\nTotal chunks: {len(all_chunks)}")
    return all_chunks

def store_in_qdrant(chunks):
    # Create collection if not exists
    existing = [c.name for c in client.get_collections().collections]
    
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=1536,
                distance=Distance.COSINE
            )
        )
        print(f"Collection '{COLLECTION_NAME}' created ")
    else:
        print(f"Collection '{COLLECTION_NAME}' already exists ")

    # Embed and store
    points = []
    for chunk_index,chunk in enumerate(chunks):
        vector = embeddings.embed_query(chunk.page_content)
        source_file=chunk.metadata.get("source","unknown")
        page=chunk.metadata.get("page",0)
        raw_id = f"{source_file}_{page}_{chunk_index}"
        point_id = hashlib.md5(raw_id.encode()).hexdigest()#deterministic (fixed) and effectively unique ID for each chunk
        point = PointStruct(
            id=point_id, 
            vector=vector,
            payload={
                "text": chunk.page_content,
                "metadata":{
                    "source": source_file,
                    "page": page,
                    "chunk_index": chunk_index
                }
                
            }
        )
        points.append(point)

    # Upload in batches of 100
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i+batch_size]
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=batch
        )
        print(f"Uploaded batch {i//batch_size + 1} ")

    print(f"\nAll {len(points)} chunks stored in Qdrant! 🚀")

if __name__ == "__main__":
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        print("Collection not found - running ingestion...")
        chunks = load_and_chunk_pdfs()
        store_in_qdrant(chunks)
    else:
        print("Collection already exists - skipping ingestion ✅")
