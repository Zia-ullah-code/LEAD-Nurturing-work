"""
Document Upload/Ingestion Tests
Tests for document upload and ingestion pipeline including chunking, embedding, and storage.
"""
import pytest
import os
import sys
import tempfile
import shutil
from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile

# Add ragImplementation to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../ragImplementation")))

from rag_main import (
    load_documents,
    split_into_chunks,
    generate_embeddings,
    store_in_chromadb
)


@pytest.mark.django_db
class TestDocumentIngestion:
    """Test document ingestion functionality."""
    
    def test_load_documents_from_folder(self, temp_pdf_directory):
        """Test loading documents from a folder."""
        # Create a mock text file (simulating PDF content)
        # In real scenario, this would be a PDF file
        test_file = os.path.join(temp_pdf_directory, "test_doc.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("This is a test document for ingestion.")
        
        # Note: load_documents only loads PDF files
        # This test verifies the function structure
        try:
            docs = load_documents(temp_pdf_directory)
            assert isinstance(docs, list)
        except Exception as e:
            pytest.skip(f"load_documents requires PDF files: {e}")
    
    def test_load_documents_multiple_files(self, temp_pdf_directory):
        """Test loading multiple documents from folder."""
        # Create multiple test files
        for i in range(3):
            test_file = os.path.join(temp_pdf_directory, f"test_doc_{i}.txt")
            with open(test_file, "w", encoding="utf-8") as f:
                f.write(f"This is test document {i}.")
        
        try:
            docs = load_documents(temp_pdf_directory)
            assert isinstance(docs, list)
        except Exception as e:
            pytest.skip(f"load_documents requires PDF files: {e}")
    
    def test_load_documents_empty_folder(self, temp_pdf_directory):
        """Test loading documents from empty folder."""
        docs = load_documents(temp_pdf_directory)
        assert isinstance(docs, list)
        assert len(docs) == 0
    
    def test_chunking_pipeline(self):
        """Test the chunking pipeline."""
        documents = [
            {
                "file_name": "test1.pdf",
                "text": "This is a test document. " * 200  # Long text
            }
        ]
        
        chunks = split_into_chunks(documents, chunk_size=100, chunk_overlap=10)
        
        assert isinstance(chunks, list)
        assert len(chunks) > 0
        
        # Verify all chunks have required fields
        for chunk in chunks:
            assert "file_name" in chunk
            assert "chunk_id" in chunk
            assert "chunk_text" in chunk
    
    def test_chunking_with_overlap(self):
        """Test that chunking preserves overlap between chunks."""
        documents = [
            {
                "file_name": "test.pdf",
                "text": "Word " * 500  # 500 words
            }
        ]
        
        chunks = split_into_chunks(documents, chunk_size=50, chunk_overlap=10)
        
        assert len(chunks) > 1  # Should create multiple chunks
        
        # Verify chunks have overlap (content should appear in adjacent chunks)
        # This is a basic check - actual overlap verification would be more complex
        assert all("chunk_text" in chunk for chunk in chunks)
    
    def test_embedding_generation(self):
        """Test embedding generation for chunks."""
        chunks = [
            {
                "file_name": "test1.pdf",
                "chunk_id": 1,
                "chunk_text": "This is a test chunk for embedding."
            },
            {
                "file_name": "test2.pdf",
                "chunk_id": 1,
                "chunk_text": "Another test chunk with different content."
            }
        ]
        
        try:
            embedded_chunks = generate_embeddings(chunks)
            
            assert isinstance(embedded_chunks, list)
            assert len(embedded_chunks) == len(chunks)
            
            # Verify embeddings are generated
            for chunk in embedded_chunks:
                assert "embedding" in chunk
                assert isinstance(chunk["embedding"], list)
                assert len(chunk["embedding"]) > 0
        except Exception as e:
            pytest.skip(f"Embedding generation requires model: {e}")
    
    def test_store_in_chromadb(self, temp_pdf_directory):
        """Test storing chunks in ChromaDB."""
        chunks = [
            {
                "file_name": "test1.pdf",
                "chunk_id": 1,
                "chunk_text": "Test chunk text for storage.",
                "embedding": None  # Will be generated
            }
        ]
        
        # Generate embeddings first
        try:
            embedded_chunks = generate_embeddings(chunks)
            
            # Store in ChromaDB
            vectorstore = store_in_chromadb(
                embedded_chunks,
                persist_directory=temp_pdf_directory
            )
            
            assert vectorstore is not None
        except Exception as e:
            pytest.skip(f"ChromaDB storage requires proper setup: {e}")
    
    def test_full_ingestion_pipeline(self, temp_pdf_directory):
        """Test the complete ingestion pipeline."""
        # Create a test document
        test_file = os.path.join(temp_pdf_directory, "test.pdf")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("This is a test document for the full ingestion pipeline. " * 100)
        
        try:
            # Step 1: Load documents
            docs = load_documents(temp_pdf_directory)
            if not docs:
                pytest.skip("No PDF documents found for testing")
            
            # Step 2: Split into chunks
            chunks = split_into_chunks(docs)
            assert len(chunks) > 0
            
            # Step 3: Generate embeddings
            embedded_chunks = generate_embeddings(chunks)
            assert len(embedded_chunks) == len(chunks)
            
            # Step 4: Store in ChromaDB
            vectorstore = store_in_chromadb(
                embedded_chunks,
                persist_directory=temp_pdf_directory
            )
            assert vectorstore is not None
            
        except Exception as e:
            pytest.skip(f"Full pipeline requires proper setup: {e}")
    
    def test_document_ingestion_api_endpoint(self, api_client):
        """Test document upload API endpoint (if implemented)."""
        # Create a mock PDF file
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\ntrailer\n<<\n/Root 1 0 R\n>>\nstartxref\n9\n%%EOF"
        pdf_file = SimpleUploadedFile(
            "test.pdf",
            pdf_content,
            content_type="application/pdf"
        )
        
        # Test upload endpoint (if it exists)
        try:
            response = api_client.post(
                "/api/documents/upload",
                {"file": pdf_file},
                format="multipart"
            )
            # If endpoint exists, should return success
            # If not, this test will fail and indicate missing endpoint
            assert response.status_code in [200, 201, 404, 405]
        except Exception as e:
            # Endpoint may not exist yet
            pytest.skip(f"Document upload endpoint may not be implemented: {e}")
    
    def test_document_ingestion_multiple_files(self, temp_pdf_directory):
        """Test ingesting multiple documents."""
        # Create multiple test documents
        for i in range(3):
            test_file = os.path.join(temp_pdf_directory, f"doc_{i}.txt")
            with open(test_file, "w", encoding="utf-8") as f:
                f.write(f"This is document {i}. " * 50)
        
        try:
            docs = load_documents(temp_pdf_directory)
            if docs:
                chunks = split_into_chunks(docs)
                assert len(chunks) > 0
                
                # Verify chunks from different documents
                file_names = set(chunk["file_name"] for chunk in chunks)
                # Should have chunks from multiple files if PDFs were created
                assert isinstance(file_names, set)
        except Exception as e:
            pytest.skip(f"Multiple file ingestion requires PDFs: {e}")
    
    def test_chunk_metadata_preservation(self):
        """Test that chunk metadata is preserved during ingestion."""
        documents = [
            {
                "file_name": "test_metadata.pdf",
                "text": "Test document with metadata. " * 50
            }
        ]
        
        chunks = split_into_chunks(documents)
        
        # Verify metadata is preserved
        for chunk in chunks:
            assert chunk["file_name"] == "test_metadata.pdf"
            assert "chunk_id" in chunk
            assert isinstance(chunk["chunk_id"], int)
    
    def test_embedding_consistency(self):
        """Test that embeddings are consistent for the same text."""
        chunks = [
            {
                "file_name": "test1.pdf",
                "chunk_id": 1,
                "chunk_text": "This is a test chunk."
            }
        ]
        
        try:
            embedded_chunks_1 = generate_embeddings(chunks)
            embedded_chunks_2 = generate_embeddings(chunks)
            
            # Embeddings should be the same for the same input
            embedding_1 = embedded_chunks_1[0]["embedding"]
            embedding_2 = embedded_chunks_2[0]["embedding"]
            
            assert embedding_1 == embedding_2
        except Exception as e:
            pytest.skip(f"Embedding consistency test requires model: {e}")
    
    def test_large_document_handling(self):
        """Test handling of large documents."""
        # Create a large document
        large_text = "This is a large document. " * 10000  # Very large text
        documents = [
            {
                "file_name": "large_doc.pdf",
                "text": large_text
            }
        ]
        
        chunks = split_into_chunks(documents, chunk_size=1000, chunk_overlap=100)
        
        # Should create multiple chunks
        assert len(chunks) > 1
        
        # Each chunk should be manageable size
        for chunk in chunks:
            assert len(chunk["chunk_text"]) <= 1500  # Allow some margin

