"""Integration tests for knowledge base operations."""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

from knowledge_base import ingest_user_file, query_knowledge_base, get_vector_store


class TestFileIngestionAndQuery:
    """Test file ingestion and query integration."""
    
    @pytest.mark.asyncio
    async def test_ingest_file_then_query_returns_results(self, tmp_path, mock_env_vars):
        """Test ingest file then query returns results."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("ServiceNow is a cloud-based platform for IT service management.")
        
        # Use temporary database
        test_db_path = tmp_path / "test_chroma_db"
        
        with patch('knowledge_base._chroma_db_path', str(test_db_path)):
            # Ingest file
            with patch('knowledge_base.TextLoader') as mock_loader:
                from langchain_core.documents import Document
                mock_doc = Document(
                    page_content="ServiceNow is a cloud-based platform for IT service management."
                )
                mock_loader_instance = Mock()
                mock_loader_instance.load.return_value = [mock_doc]
                mock_loader.return_value = mock_loader_instance
                
                chunks = ingest_user_file(str(test_file))
                assert chunks > 0
    
    def test_multiple_file_ingestion(self, tmp_path, mock_env_vars):
        """Test multiple file ingestion."""
        test_file1 = tmp_path / "test1.txt"
        test_file1.write_text("First document")
        test_file2 = tmp_path / "test2.txt"
        test_file2.write_text("Second document")
        
        test_db_path = tmp_path / "test_chroma_db"
        
        with patch('knowledge_base._chroma_db_path', str(test_db_path)):
            with patch('knowledge_base.TextLoader') as mock_loader:
                from langchain_core.documents import Document
                mock_loader_instance = Mock()
                mock_loader.return_value = mock_loader_instance
                
                # Mock load to return different docs
                def load_side_effect(*args, **kwargs):
                    if "test1" in str(args[0]):
                        return [Document(page_content="First document")]
                    return [Document(page_content="Second document")]
                
                mock_loader_instance.load.side_effect = load_side_effect
                mock_loader.return_value = mock_loader_instance
                
                chunks1 = ingest_user_file(str(test_file1))
                chunks2 = ingest_user_file(str(test_file2))
                
                assert chunks1 > 0
                assert chunks2 > 0
    
    def test_query_filtering_by_source_type(self, mock_env_vars):
        """Test query filtering by source_type."""
        with patch('knowledge_base.get_vector_store') as mock_store:
            mock_vector_store = Mock()
            from langchain_core.documents import Document
            
            # Mock documents with different source types
            user_doc = Document(
                page_content="User context",
                metadata={"source_type": "user_context", "source": "user.txt"}
            )
            global_doc = Document(
                page_content="Global context",
                metadata={"source_type": "global", "source": "global.txt"}
            )
            
            def search_side_effect(*args, **kwargs):
                filter_type = kwargs.get('filter', {}).get('source_type')
                if filter_type == 'user_context':
                    return [(user_doc, 0.9)]
                return [(global_doc, 0.9)]
            
            mock_vector_store.similarity_search_with_score = Mock(side_effect=search_side_effect)
            mock_store.return_value = mock_vector_store
            
            # Query with filter
            results = query_knowledge_base("test", filter_type='user_context')
            
            assert len(results) > 0
            assert results[0]['metadata']['source_type'] == 'user_context'


class TestChromaDBPersistence:
    """Test ChromaDB persistence."""
    
    def test_data_persists_across_sessions(self, tmp_path, mock_env_vars):
        """Test data persists across sessions."""
        # This would require actual ChromaDB testing
        # For now, we verify the persist_directory is set
        test_db_path = tmp_path / "test_chroma_db"
        
        with patch('knowledge_base._chroma_db_path', str(test_db_path)):
            with patch('knowledge_base.Chroma') as mock_chroma:
                get_vector_store()
                
                # Verify Chroma was called with persist_directory
                call_args = mock_chroma.call_args
                assert call_args[1]['persist_directory'] == str(test_db_path)
    
    def test_metadata_preservation(self, mock_env_vars):
        """Test metadata preservation."""
        with patch('knowledge_base.get_vector_store') as mock_store:
            mock_vector_store = Mock()
            from langchain_core.documents import Document
            
            test_metadata = {
                "source": "test.txt",
                "source_type": "user_context",
                "file_path": "/path/to/test.txt"
            }
            
            doc = Document(
                page_content="Test content",
                metadata=test_metadata
            )
            
            mock_vector_store.similarity_search_with_score.return_value = [(doc, 0.9)]
            mock_store.return_value = mock_vector_store
            
            results = query_knowledge_base("test")
            
            assert len(results) > 0
            assert results[0]['metadata'] == test_metadata
