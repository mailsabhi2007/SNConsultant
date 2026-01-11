"""Knowledge base implementation using ChromaDB for RAG."""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# Load environment variables from .env file
load_dotenv()


# Initialize embeddings
_embeddings = None
_vector_store = None
_chroma_db_path = "./chroma_db"


def get_embeddings():
    """Get or create OpenAI embeddings instance."""
    global _embeddings
    if _embeddings is None:
        # Check if API key is set
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set. "
                "Please add it to your .env file."
            )
        _embeddings = OpenAIEmbeddings()
    return _embeddings


def get_vector_store():
    """Get or create Chroma vector store instance."""
    global _vector_store
    if _vector_store is None:
        embeddings = get_embeddings()
        # Create chroma_db directory if it doesn't exist
        Path(_chroma_db_path).mkdir(parents=True, exist_ok=True)
        
        # Initialize or load existing Chroma vector store
        _vector_store = Chroma(
            persist_directory=_chroma_db_path,
            embedding_function=embeddings,
        )
    return _vector_store


def ingest_user_file(file_path: str):
    """
    Ingest a user-provided file (PDF or Text) into the knowledge base.
    
    Args:
        file_path: Path to the PDF or text file to ingest
        
    Returns:
        Number of chunks created
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    print(f"Loading user file: {file_path}")
    
    # Determine file type and load accordingly
    file_extension = file_path.suffix.lower()
    
    if file_extension == '.pdf':
        loader = PyPDFLoader(str(file_path))
    elif file_extension in ['.txt', '.text', '.csv']:
        loader = TextLoader(str(file_path))
    else:
        raise ValueError(
            f"Unsupported file type: {file_extension}. "
            "Supported types: .pdf, .txt, .text, .csv"
        )
    
    # Load documents
    documents = loader.load()
    
    if not documents:
        print("No content found in file.")
        return 0
    
    print(f"Loaded {len(documents)} documents from file")
    
    # Split documents
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    chunks = text_splitter.split_documents(documents)
    
    # Add metadata to all chunks
    for chunk in chunks:
        chunk.metadata['source_type'] = 'user_context'
        chunk.metadata['source'] = str(file_path.name)
        # Preserve original file path
        if 'file_path' not in chunk.metadata:
            chunk.metadata['file_path'] = str(file_path)
    
    print(f"Split into {len(chunks)} chunks")
    
    # Add to vector store
    vector_store = get_vector_store()
    vector_store.add_documents(chunks)
    
    # Note: Chroma 0.4.x automatically persists, no need to call persist()
    
    print(f"Successfully ingested {len(chunks)} chunks from {file_path.name}")
    return len(chunks)


def query_knowledge_base(
    query: str,
    filter_type: Optional[str] = None,
    k: int = 3
) -> List[Dict[str, Any]]:
    """
    Query the knowledge base and return relevant chunks.
    
    Args:
        query: The search query
        filter_type: Optional filter by source_type ('global' or 'user_context')
        k: Number of results to return (default: 3)
        
    Returns:
        List of dictionaries containing:
        - content: The chunk text
        - source: The source of the chunk
        - metadata: Full metadata dictionary
        - score: Similarity score (if available)
    """
    vector_store = get_vector_store()
    
    # Build filter if filter_type is provided
    where_filter = None
    if filter_type:
        where_filter = {"source_type": filter_type}
    
    # Perform similarity search
    try:
        if where_filter:
            # Try different filter parameter names for ChromaDB
            # LangChain's Chroma integration may vary
            try:
                # Try 'filter' parameter first
                results = vector_store.similarity_search_with_score(
                    query,
                    k=k,
                    filter=where_filter
                )
            except (TypeError, AttributeError):
                try:
                    # Try 'where' parameter
                    results = vector_store.similarity_search_with_score(
                        query,
                        k=k,
                        where=where_filter
                    )
                except (TypeError, AttributeError):
                    # Fallback: search all and filter manually
                    all_results = vector_store.similarity_search_with_score(query, k=k*5)
                    results = [
                        (doc, score) for doc, score in all_results
                        if doc.metadata.get('source_type') == filter_type
                    ][:k]
        else:
            results = vector_store.similarity_search_with_score(query, k=k)
    except Exception as e:
        print(f"Error querying knowledge base: {e}")
        return []
    
    # Format results
    formatted_results = []
    for doc, score in results:
        result = {
            "content": doc.page_content,
            "source": doc.metadata.get("source", "Unknown"),
            "metadata": doc.metadata,
            "score": float(score) if score is not None else None
        }
        formatted_results.append(result)
    
    return formatted_results


def clear_knowledge_base():
    """Clear all documents from the knowledge base."""
    import shutil
    
    if Path(_chroma_db_path).exists():
        shutil.rmtree(_chroma_db_path)
        print(f"Cleared knowledge base at {_chroma_db_path}")
        global _vector_store
        _vector_store = None
    else:
        print("Knowledge base is already empty")


def get_knowledge_base_stats() -> Dict[str, Any]:
    """Get statistics about the knowledge base."""
    try:
        vector_store = get_vector_store()
        # Get collection to access stats
        collection = vector_store._collection
        
        count = collection.count()
        
        # Get unique source types
        results = collection.get()
        source_types = set()
        sources = set()
        
        if results and 'metadatas' in results:
            for metadata in results.get('metadatas', []):
                if metadata:
                    if 'source_type' in metadata:
                        source_types.add(metadata['source_type'])
                    if 'source' in metadata:
                        sources.add(metadata['source'])
        
        return {
            "total_chunks": count,
            "source_types": list(source_types),
            "unique_sources": len(sources),
            "sources": list(sources)[:10]  # First 10 sources
        }
    except Exception as e:
        return {"error": str(e)}


def get_indexed_files() -> List[Dict[str, Any]]:
    """
    Get list of all indexed files with metadata.
    
    Returns:
        List of dictionaries containing file information:
        - filename: Name of the file
        - source: Source identifier
        - chunk_count: Number of chunks for this file
        - source_type: Type of source (e.g., 'user_context')
    """
    try:
        vector_store = get_vector_store()
        collection = vector_store._collection
        
        # Get all documents
        results = collection.get()
        
        if not results or 'metadatas' not in results:
            return []
        
        # Group by source
        file_info = {}
        for metadata in results.get('metadatas', []):
            if metadata and 'source' in metadata:
                source = metadata['source']
                source_type = metadata.get('source_type', 'unknown')
                
                if source not in file_info:
                    file_info[source] = {
                        'filename': source,
                        'source': source,
                        'chunk_count': 0,
                        'source_type': source_type
                    }
                file_info[source]['chunk_count'] += 1
        
        # Filter for user_context files only
        user_files = [
            info for info in file_info.values()
            if info['source_type'] == 'user_context'
        ]
        
        return user_files
    except Exception as e:
        print(f"Error getting indexed files: {e}")
        return []


def remove_file_from_kb(filename: str) -> bool:
    """
    Remove all chunks for a specific file from the knowledge base.
    
    Args:
        filename: Name of the file to remove (matches 'source' metadata)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        vector_store = get_vector_store()
        collection = vector_store._collection
        
        # Get all document IDs and metadata
        results = collection.get()
        
        if not results or 'ids' not in results or 'metadatas' not in results:
            return False
        
        # Find IDs to delete (where source matches filename)
        ids_to_delete = []
        for i, metadata in enumerate(results.get('metadatas', [])):
            if metadata and metadata.get('source') == filename:
                doc_id = results['ids'][i]
                ids_to_delete.append(doc_id)
        
        if not ids_to_delete:
            return False
        
        # Delete the documents
        collection.delete(ids=ids_to_delete)
        
        return True
    except Exception as e:
        print(f"Error removing file from knowledge base: {e}")
        return False


def get_file_metadata() -> Dict[str, Any]:
    """
    Get metadata about indexed files.
    
    Returns:
        Dictionary with file counts and source information
    """
    files = get_indexed_files()
    return {
        "total_files": len(files),
        "total_chunks": sum(f.get('chunk_count', 0) for f in files),
        "files": files
    }


if __name__ == "__main__":
    # Example usage
    print("Knowledge Base Test")
    print("=" * 80)
    
    # Note: Global documentation is now accessed via live search (consult_public_docs tool)
    # User files can be ingested using ingest_user_file()
    print("\n1. Global documentation is accessed via live search when needed.")
    
    # Get stats
    print("\n2. Knowledge base statistics:")
    stats = get_knowledge_base_stats()
    print(f"   {stats}")
    
    # Query example
    print("\n3. Querying knowledge base...")
    results = query_knowledge_base("What is incident management?", k=3)
    for i, result in enumerate(results, 1):
        print(f"\n   Result {i}:")
        print(f"   Source: {result['source']}")
        print(f"   Score: {result['score']}")
        print(f"   Content: {result['content'][:200]}...")
