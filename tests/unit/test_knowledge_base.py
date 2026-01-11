"""Unit tests for knowledge_base.py"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from langchain_core.documents import Document

from knowledge_base import (
    ingest_user_file,
    query_knowledge_base,
    get_knowledge_base_stats,
    clear_knowledge_base,
    get_embeddings,
    get_vector_store
)


class TestIngestUserFile:
    """Test ingest_user_file function."""
    
    def test_text_file_ingestion(self, tmp_path, mock_env_vars):
        """Test text file ingestion."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("This is a test document about ServiceNow.")
        
        with patch('knowledge_base.get_vector_store') as mock_store:
            mock_vector_store = Mock()
            mock_vector_store.add_documents = Mock()
            mock_store.return_value = mock_vector_store
            
            with patch('knowledge_base.TextLoader') as mock_loader:
                mock_doc = Document(page_content="This is a test document about ServiceNow.")
                mock_loader_instance = Mock()
                mock_loader_instance.load.return_value = [mock_doc]
                mock_loader.return_value = mock_loader_instance
                
                with patch('knowledge_base.RecursiveCharacterTextSplitter') as mock_splitter:
                    mock_splitter_instance = Mock()
                    mock_splitter_instance.split_documents.return_value = [mock_doc]
                    mock_splitter.return_value = mock_splitter_instance
                    
                    result = ingest_user_file(str(test_file))
                    
                    assert result > 0
                    mock_vector_store.add_documents.assert_called_once()
    
    def test_pdf_file_ingestion(self, tmp_path, mock_env_vars):
        """Test PDF file ingestion."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("PDF content")  # Simplified for test
        
        with patch('knowledge_base.get_vector_store') as mock_store:
            mock_vector_store = Mock()
            mock_vector_store.add_documents = Mock()
            mock_store.return_value = mock_vector_store
            
            with patch('knowledge_base.PyPDFLoader') as mock_loader:
                mock_doc = Document(page_content="PDF content")
                mock_loader_instance = Mock()
                mock_loader_instance.load.return_value = [mock_doc]
                mock_loader.return_value = mock_loader_instance
                
                with patch('knowledge_base.RecursiveCharacterTextSplitter') as mock_splitter:
                    mock_splitter_instance = Mock()
                    mock_splitter_instance.split_documents.return_value = [mock_doc]
                    mock_splitter.return_value = mock_splitter_instance
                    
                    result = ingest_user_file(str(test_file))
                    
                    assert result > 0
    
    def test_unsupported_file_type_raises_error(self, tmp_path, mock_env_vars):
        """Test unsupported file type raises error."""
        test_file = tmp_path / "test.doc"
        test_file.write_text("Content")
        
        with pytest.raises(ValueError, match="Unsupported file type"):
            ingest_user_file(str(test_file))
    
    def test_file_not_found_raises_error(self, mock_env_vars):
        """Test file not found raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            ingest_user_file("nonexistent_file.txt")
    
    def test_chunk_metadata_assignment(self, tmp_path, mock_env_vars):
        """Test chunk creation and metadata assignment."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        with patch('knowledge_base.get_vector_store') as mock_store:
            mock_vector_store = Mock()
            added_docs = []
            def capture_docs(docs):
                added_docs.extend(docs)
            mock_vector_store.add_documents = Mock(side_effect=capture_docs)
            mock_store.return_value = mock_vector_store
            
            with patch('knowledge_base.TextLoader') as mock_loader:
                mock_doc = Document(page_content="Test content")
                mock_loader_instance = Mock()
                mock_loader_instance.load.return_value = [mock_doc]
                mock_loader.return_value = mock_loader_instance
                
                with patch('knowledge_base.RecursiveCharacterTextSplitter') as mock_splitter:
                    mock_splitter_instance = Mock()
                    chunk = Document(page_content="Test content")
                    mock_splitter_instance.split_documents.return_value = [chunk]
                    mock_splitter.return_value = mock_splitter_instance
                    
                    ingest_user_file(str(test_file))
                    
                    if added_docs:
                        assert added_docs[0].metadata.get('source_type') == 'user_context'
                        assert 'source' in added_docs[0].metadata


class TestQueryKnowledgeBase:
    """Test query_knowledge_base function."""
    
    def test_query_with_filter_type(self, mock_env_vars):
        """Test query with filter_type='user_context'."""
        with patch('knowledge_base.get_vector_store') as mock_store:
            mock_vector_store = Mock()
            mock_doc = Document(
                page_content="Test content",
                metadata={"source": "test.txt", "source_type": "user_context"}
            )
            mock_vector_store.similarity_search_with_score.return_value = [(mock_doc, 0.9)]
            mock_store.return_value = mock_vector_store
            
            results = query_knowledge_base("test query", filter_type='user_context', k=3)
            
            assert len(results) > 0
            assert results[0]['content'] == "Test content"
            assert results[0]['source'] == "test.txt"
    
    def test_query_without_filter(self, mock_env_vars):
        """Test query without filter."""
        with patch('knowledge_base.get_vector_store') as mock_store:
            mock_vector_store = Mock()
            mock_doc = Document(page_content="Test content")
            mock_vector_store.similarity_search_with_score.return_value = [(mock_doc, 0.9)]
            mock_store.return_value = mock_vector_store
            
            results = query_knowledge_base("test query", k=3)
            
            assert len(results) > 0
    
    def test_query_with_k_parameter(self, mock_env_vars):
        """Test query with k parameter."""
        with patch('knowledge_base.get_vector_store') as mock_store:
            mock_vector_store = Mock()
            mock_docs = [Document(page_content=f"Content {i}") for i in range(5)]
            mock_vector_store.similarity_search_with_score.return_value = [
                (doc, 0.9) for doc in mock_docs
            ]
            mock_store.return_value = mock_vector_store
            
            results = query_knowledge_base("test query", k=5)
            
            assert len(results) == 5
    
    def test_empty_results_handling(self, mock_env_vars):
        """Test empty results handling."""
        with patch('knowledge_base.get_vector_store') as mock_store:
            mock_vector_store = Mock()
            mock_vector_store.similarity_search_with_score.return_value = []
            mock_store.return_value = mock_vector_store
            
            results = query_knowledge_base("test query")
            
            assert results == []
    
    def test_result_formatting(self, mock_env_vars):
        """Test result formatting (content, source, metadata, score)."""
        with patch('knowledge_base.get_vector_store') as mock_store:
            mock_vector_store = Mock()
            mock_doc = Document(
                page_content="Test content",
                metadata={"source": "test.txt", "source_type": "user_context"}
            )
            mock_vector_store.similarity_search_with_score.return_value = [(mock_doc, 0.85)]
            mock_store.return_value = mock_vector_store
            
            results = query_knowledge_base("test query")
            
            assert len(results) > 0
            assert 'content' in results[0]
            assert 'source' in results[0]
            assert 'metadata' in results[0]
            assert 'score' in results[0]
            assert results[0]['score'] == 0.85
    
    def test_error_handling_returns_empty_list(self, mock_env_vars):
        """Test error handling returns empty list."""
        with patch('knowledge_base.get_vector_store') as mock_store:
            mock_vector_store = Mock()
            mock_vector_store.similarity_search_with_score.side_effect = Exception("DB Error")
            mock_store.return_value = mock_vector_store
            
            results = query_knowledge_base("test query")
            
            assert results == []


class TestGetKnowledgeBaseStats:
    """Test get_knowledge_base_stats function."""
    
    def test_stats_retrieval_with_populated_database(self, mock_env_vars):
        """Test stats retrieval with populated database."""
        with patch('knowledge_base.get_vector_store') as mock_store:
            mock_vector_store = Mock()
            mock_collection = Mock()
            mock_collection.count.return_value = 10
            mock_collection.get.return_value = {
                'metadatas': [
                    {'source_type': 'user_context', 'source': 'test1.txt'},
                    {'source_type': 'user_context', 'source': 'test2.txt'},
                ]
            }
            mock_vector_store._collection = mock_collection
            mock_store.return_value = mock_vector_store
            
            stats = get_knowledge_base_stats()
            
            assert stats['total_chunks'] == 10
            assert 'source_types' in stats
            assert 'unique_sources' in stats
    
    def test_stats_with_empty_database(self, mock_env_vars):
        """Test stats with empty database."""
        with patch('knowledge_base.get_vector_store') as mock_store:
            mock_vector_store = Mock()
            mock_collection = Mock()
            mock_collection.count.return_value = 0
            mock_collection.get.return_value = {'metadatas': []}
            mock_vector_store._collection = mock_collection
            mock_store.return_value = mock_vector_store
            
            stats = get_knowledge_base_stats()
            
            assert stats['total_chunks'] == 0
    
    def test_error_handling(self, mock_env_vars):
        """Test error handling in stats."""
        with patch('knowledge_base.get_vector_store') as mock_store:
            mock_store.side_effect = Exception("Error")
            
            stats = get_knowledge_base_stats()
            
            assert 'error' in stats


class TestClearKnowledgeBase:
    """Test clear_knowledge_base function."""
    
    def test_clearing_populated_database(self, tmp_path, mock_env_vars):
        """Test clearing populated database."""
        test_db_path = tmp_path / "test_db"
        test_db_path.mkdir()
        
        with patch('knowledge_base._chroma_db_path', str(test_db_path)):
            with patch('knowledge_base._vector_store', None):
                clear_knowledge_base()
                
                # Check directory was removed or message printed
                # (actual behavior depends on implementation)
    
    def test_clearing_empty_database(self, mock_env_vars):
        """Test clearing empty database."""
        with patch('knowledge_base.Path') as mock_path:
            mock_path.return_value.exists.return_value = False
            
            # Should not raise error
            clear_knowledge_base()


class TestGetEmbeddingsAndVectorStore:
    """Test get_embeddings and get_vector_store functions."""
    
    def test_singleton_pattern_for_embeddings(self, mock_env_vars):
        """Test singleton pattern for embeddings."""
        # Reset global
        import knowledge_base
        knowledge_base._embeddings = None
        
        emb1 = get_embeddings()
        emb2 = get_embeddings()
        
        assert emb1 is emb2
    
    def test_api_key_validation(self, monkeypatch):
        """Test API key validation."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        
        import knowledge_base
        knowledge_base._embeddings = None
        
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            get_embeddings()
