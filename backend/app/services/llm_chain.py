import os
import sys
sys.path.append(os.path.dirname(__file__))
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

try:
    from retriever import retrieve_chunks
    from cache import get_cached_response, set_cached_response
except ImportError:
    from app.services.retriever import retrieve_chunks
    from app.services.cache import get_cached_response, set_cached_response
load_dotenv()

# Init LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,        # Deterministic - no random answers
)

# System prompt - our guardrail
SYSTEM_PROMPT = """You are HarshGPT, a helpful AI assistant that answers questions about Harsh Nandan Shukla based strictly on the provided context from his resume, internship reports and project reports.

Instructions:
- Answer ONLY using information from the context below
- Be concise and professional
- Mention which document the information comes from
- If the question is completely unrelated to Harsh's documents (like "capital of France"), then say "I can only answer questions about Harsh's projects and internship reports."
- If the context contains relevant information, ALWAYS use it to answer

Context:
{context}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{question}")
])

# Chain
chain = prompt | llm | StrOutputParser()
RESUME_KEYWORDS = [
    "skills", "experience", "education", "languages", 
    "tools", "frameworks", "cgpa", "degree", "courses",
    "qualification", "programming", "tech stack"
]

def get_source_filter(query: str):
    query_lower = query.lower()
    if any(keyword in query_lower for keyword in RESUME_KEYWORDS):
        return "Harsh_IITJ_Resume.pdf"
    return None

GUARDRAIL_RESPONSE = "I can only answer questions about Harsh's projects and internship reports."

def get_answer(query: str, source_filter: str = None) -> dict:
    """
    Full RAG pipeline:
    1. Retrieve relevant chunks
    2. Build context
    3. Generate answer
    """
    if not source_filter:
        source_filter = get_source_filter(query)

    cached=get_cached_response(query)
    if cached:
        return cached    
    # Step 1 - Retrieve
    chunks = retrieve_chunks(query, source_filter)

    if not chunks:
        return {
            "answer": "I couldn't find relevant information in Harsh's documents for that question.",
            "sources": []
        }

    # Step 2 - Build context from chunks
    context = "\n\n".join([
        f"[Source: {chunk.metadata.get('source')} | Page: {chunk.metadata.get('page')}]\n{chunk.page_content}"
        for chunk in chunks
    ])


    # Step 3 - Generate answer

    try:
        answer = chain.invoke({
        "context": context,
        "question": query
        })
    except Exception as e:
        print(f"LLM Error: {e}")
        return{
            "answer": "I'm having trouble generating an answer right now. Please try again.",
            "sources": [],
            "error": str(e)  

        }
    if answer == GUARDRAIL_RESPONSE:
        return{
            "answer":answer,
            "sources":[]
        }

    # Step 4 - Build sources list
        # if same source for multiple chunks we don't want repetition as it will make result to user via fast api messy so we use tuple
        # set of tuples  (no repitition)
    sources = list({
        (chunk.metadata.get("source"),chunk.metadata.get("page"))
        for chunk in chunks
    })
    # list of dictionaries
    sources=[
        {"source":s,"page":p}
        for s,p in sources
    ]

    result= {
        "answer": answer,
        "sources": sources
    }
    set_cached_response(query, result)
    return result






