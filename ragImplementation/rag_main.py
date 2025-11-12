import os
import re
import pdfplumber
from PyPDF2 import PdfReader

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Use environment variable if set (for Render), otherwise use local path
CHROMA_DB_PATH = os.environ.get('CHROMA_DB_PATH', os.path.join(BASE_DIR, "chroma_db"))
RAG_PDFS_PATH = os.environ.get('RAG_PDFS_PATH', os.path.join(BASE_DIR, "pdfs"))


def load_documents(folder_path):
    print("----------------------------------step1: pdf to text----------------------------------")

    """
    Loads all PDF files from a folder and extracts their text.

    Args:
        folder_path (str): Path to the folder containing PDF files.

    Returns:
        list[dict]: A list of dictionaries, each containing:
            - 'file_name': name of the PDF file
            - 'text': extracted text content
    """
    documents = []

    # Loop through all files in the folder
    if not os.path.exists(folder_path):
        print(f"Warning: Folder not found: {folder_path}")
        return documents

    for file_name in os.listdir(folder_path):
        if file_name.lower().endswith('.pdf'):
            file_path = os.path.join(folder_path, file_name)
            text = ""

            try:
                # First try with pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text() or ""
                        text += page_text + "\n"

            except Exception as e:
                # Fallback to PyPDF2 if pdfplumber fails
                try:
                    with open(file_path, 'rb') as f:
                        reader = PdfReader(f)
                        for page in reader.pages:
                            text += page.extract_text() or ""
                except Exception as inner_e:
                    print(f"Failed to read {file_name}: {inner_e}")
                    continue

            documents.append({
                "file_name": file_name,
                "text": text.strip()
            })

    return documents



from langchain.text_splitter import RecursiveCharacterTextSplitter


def split_into_chunks(documents, chunk_size=1000, chunk_overlap=100):
    print("----------------------------------step2: spliting into chunks----------------------------------")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    chunks = []

    for doc in documents:
        file_name = doc["file_name"]
        text = doc["text"]

        if not text.strip():
            continue

        split_texts = text_splitter.split_text(text)

        for i, chunk in enumerate(split_texts):
            chunks.append({
                "file_name": file_name,
                "chunk_id": i + 1,
                "chunk_text": chunk
            })

    return chunks



from langchain_community.embeddings import HuggingFaceEmbeddings

def generate_embeddings(chunks):
    print("----------------------------------step3: generating embeddings----------------------------------")

    """
    Generates embeddings for each text chunk using a local model
    (sentence-transformers/all-MiniLM-L6-v2).

    Args:
        chunks (list[dict]): List of chunks with keys:
                             - 'file_name'
                             - 'chunk_id'
                             - 'chunk_text'

    Returns:
        list[dict]: Each dict contains:
                    - 'file_name'
                    - 'chunk_id'
                    - 'chunk_text'
                    - 'embedding' (list of floats)
    """
    # Initialize the local embedding model
    embeddings_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    embedded_chunks = []

    for chunk in chunks:
        text = chunk["chunk_text"]
        vector = embeddings_model.embed_query(text)

        embedded_chunks.append({
            "file_name": chunk["file_name"],
            "chunk_id": chunk["chunk_id"],
            "chunk_text": text,
            "embedding": vector
        })

    return embedded_chunks



from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

def store_in_chromadb(chunks, persist_directory=CHROMA_DB_PATH):
    print("----------------------------------step4: storing in chromadb----------------------------------")

    """
    Stores all chunks and their embeddings into a persistent ChromaDB collection.

    Args:
        chunks (list[dict]): Each dict must contain:
                             - 'file_name'
                             - 'chunk_id'
                             - 'chunk_text'
                             - 'embedding'
        persist_directory (str): Folder path to persist the Chroma database.

    Returns:
        Chroma: A Chroma vector store instance.
    """
    # Initialize the same embeddings model used earlier
    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # Ensure directory exists
    os.makedirs(persist_directory, exist_ok=True)

    # Prepare data for Chroma
    ids = [f"{chunk['file_name']}_chunk{chunk['chunk_id']}" for chunk in chunks]
    texts = [chunk["chunk_text"] for chunk in chunks]
    metadatas = [{"file_name": chunk["file_name"], "chunk_id": chunk["chunk_id"]} for chunk in chunks]

    # Create or load Chroma collection
    vectorstore = Chroma.from_texts(
        texts=texts,
        embedding=embedding_model,
        metadatas=metadatas,
        ids=ids,
        persist_directory=persist_directory,
        collection_name="brochure_vectors"
    )

    # Save to disk
    vectorstore.persist()

    return vectorstore


from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

def query_brochures(query_text, top_k=3):
    """
    Search the ChromaDB 'brochure_vectors' collection for the top-k
    most relevant chunks to the given query text using cosine similarity.
    """
    # Load the same embedding model used for indexing
    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # Use environment variable if set, otherwise use default
    chroma_db_path = os.environ.get('CHROMA_DB_PATH', CHROMA_DB_PATH)
    
    # Ensure directory exists
    os.makedirs(chroma_db_path, exist_ok=True)

    # Reconnect to your ChromaDB collection
    db = Chroma(
        persist_directory=chroma_db_path,
        collection_name="brochure_vectors",
        embedding_function=embedding_model
    )

    # Perform semantic search (cosine similarity under the hood)
    results = db.similarity_search(query_text, k=top_k)

    # Display top results
    for i, r in enumerate(results, 1):
        # print(f"\n🔹 Result {i}")
        # print(f"Source: {r.metadata['file_name']} | Chunk ID: {r.metadata['chunk_id']}")
        # print(f"Text: {r.page_content[:300]}...")  # show first 300 chars
        pass  # Query matched

    return results



def build_chroma_db():
    # Use environment variable if set, otherwise use default
    folder = RAG_PDFS_PATH if os.environ.get('RAG_PDFS_PATH') else os.path.join(BASE_DIR, "pdfs")
    
    # Ensure folder exists
    if not os.path.exists(folder):
        print(f"Warning: PDF folder not found: {folder}")
        print("Creating folder...")
        os.makedirs(folder, exist_ok=True)
        print("Please add PDF files to the folder and run again.")
        return
    
    docs = load_documents(folder)
    if not docs:
        print(f"No PDF documents found in {folder}")
        return
    
    # Use environment variable for ChromaDB path
    chroma_db_path = os.environ.get('CHROMA_DB_PATH', CHROMA_DB_PATH)
    
    chunks = split_into_chunks(docs)
    embedded_chunks = generate_embeddings(chunks)
    store_in_chromadb(embedded_chunks, persist_directory=chroma_db_path)

    print("✅ Chunks successfully stored in ChromaDB!")


def query(query_text):
    # Use the actual query text passed into the function

    results = query_brochures(query_text)
    return results

if __name__ == "__main__":
    # Run once to build the Chroma database
    build_chroma_db()
    # print("📂 Using ChromaDB path:", CHROMA_DB_PATH)


    # Then perform queries dynamically
    response = query("Tell me about payment plans for Lumina Grand")


