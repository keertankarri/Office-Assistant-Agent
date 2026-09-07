import os
from dotenv import load_dotenv

# Force load environment variables from .env
load_dotenv(override=True)

from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

VECTOR_DB_DIR = "data/chroma_db"

def get_embeddings():
    # Use the active Gemini embedding model ID
    return GoogleGenerativeAIEmbeddings(model="gemini-embedding-2-preview")

def build_vector_db():
    if not os.path.exists("data/documents") or not os.listdir("data/documents"):
        print("Warning: No documents found in data/documents/")
        return None
        
    loader = PyPDFDirectoryLoader("data/documents/")
    docs = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
    splits = text_splitter.split_documents(docs)
    
    embeddings = get_embeddings()
    vectorstore = Chroma.from_documents(
        documents=splits, 
        embedding=embeddings, 
        persist_directory=VECTOR_DB_DIR
    )
    return vectorstore

def query_policy_rag(query: str):
    embeddings = get_embeddings()
    
    if not os.path.exists(VECTOR_DB_DIR):
        build_vector_db()
        
    vectorstore = Chroma(persist_directory=VECTOR_DB_DIR, embedding_function=embeddings)
    results = vectorstore.similarity_search(query, k=2)
    
    context = "\n\n".join([f"Source ({doc.metadata.get('source', 'Policy')}): {doc.page_content}" for doc in results])
    return context

if __name__ == "__main__":
    print("Building Chroma vector store with gemini-embedding-2-preview...")
    build_vector_db()
    print("Vector database built successfully!")