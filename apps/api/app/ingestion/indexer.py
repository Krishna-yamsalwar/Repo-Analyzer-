"""
Repository indexing pipeline using LlamaIndex and ChromaDB.
Handles file ingestion, chunking, and vector storage.
"""
import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.repository import Repository
from app.models.indexed_file import IndexedFile
from app.services.vector_store import get_vector_store
from app.ingestion.parser import get_parser, ParseResult

logger = logging.getLogger(__name__)

# File extensions to index
INDEXABLE_EXTENSIONS = {
    '.py', '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',
    '.java', '.kt', '.go', '.rs', '.c', '.cpp', '.h', '.hpp',
    '.rb', '.php', '.swift', '.cs', '.scala', '.sh', '.bash',
    '.sql', '.md', '.txt', '.json', '.yaml', '.yml', '.toml',
    '.html', '.css', '.scss', '.sass', '.less',
}

# Directories to skip
SKIP_DIRECTORIES = {
    'node_modules', '__pycache__', '.git', '.svn', '.hg',
    'venv', '.venv', 'env', '.env', 'dist', 'build',
    '.next', '.nuxt', '.cache', 'coverage', '.pytest_cache',
    'target', '.idea', '.vscode', '__MACOSX',
}

# Max file size (5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024


@dataclass
class IndexingStats:
    """Statistics from the indexing process."""
    total_files: int = 0
    indexed_files: int = 0
    skipped_files: int = 0
    failed_files: int = 0
    total_chunks: int = 0
    languages: Dict[str, int] = None
    
    def __post_init__(self):
        if self.languages is None:
            self.languages = {}


class RepositoryIndexer:
    """Handles the indexing of repository files."""
    
    def __init__(self, repository_id: int, db: AsyncSession):
        self.repository_id = repository_id
        self.db = db
        self.parser = get_parser()
        self.vector_store = get_vector_store(repository_id)
    
    async def index_directory(self, directory_path: str) -> IndexingStats:
        """Index all files in a directory recursively."""
        stats = IndexingStats()
        path = Path(directory_path)
        
        if not path.exists() or not path.is_dir():
            logger.error(f"Directory not found: {directory_path}")
            return stats
        
        # Collect all files to index
        files_to_index = self._collect_files(path)
        stats.total_files = len(files_to_index)
        
        logger.info(f"Found {stats.total_files} files to index in {directory_path}")
        
        # Update repository status
        await self._update_repo_status("indexing", stats)
        
        # Process each file
        for file_path in files_to_index:
            try:
                result = await self._index_file(file_path, directory_path)
                if result:
                    stats.indexed_files += 1
                    stats.total_chunks += len(result.chunks)
                    
                    # Track language stats
                    if result.language != "unknown":
                        stats.languages[result.language] = stats.languages.get(result.language, 0) + 1
                else:
                    stats.skipped_files += 1
            except Exception as e:
                logger.error(f"Failed to index {file_path}: {e}")
                stats.failed_files += 1
        
        # Update final status
        status = "ready" if stats.failed_files == 0 else "error"
        await self._update_repo_status(status, stats)
        
        logger.info(f"Indexing complete: {stats.indexed_files}/{stats.total_files} files, {stats.total_chunks} chunks")
        return stats
    
    def _collect_files(self, base_path: Path) -> List[Path]:
        """Recursively collect all indexable files."""
        files = []
        
        for item in base_path.rglob('*'):
            # Skip directories in blocklist
            if any(skip_dir in item.parts for skip_dir in SKIP_DIRECTORIES):
                continue
            
            if item.is_file():
                # Check extension
                if item.suffix.lower() in INDEXABLE_EXTENSIONS:
                    # Check file size
                    try:
                        if item.stat().st_size <= MAX_FILE_SIZE:
                            files.append(item)
                    except OSError:
                        continue
        
        return files
    
    async def _index_file(self, file_path: Path, base_dir: str) -> Optional[ParseResult]:
        """Index a single file."""
        str_path = str(file_path)
        relative_path = str(file_path.relative_to(base_dir))
        
        # Check if file already indexed with same hash
        existing = await self._get_existing_file(relative_path)
        
        # Parse file
        result = self.parser.parse_file(str_path)
        
        if result.error:
            logger.warning(f"Parse error for {str_path}: {result.error}")
            return None
        
        # Check if content changed (fingerprint comparison)
        if existing and existing.content_hash == result.content_hash:
            logger.debug(f"Skipping unchanged file: {relative_path}")
            return None
        
        # Add chunks to vector store
        if result.chunks:
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(result.chunks):
                chunk_id = f"{self.repository_id}_{relative_path}_{i}"
                documents.append(chunk['content'])
                metadatas.append({
                    'repository_id': self.repository_id,
                    'file_path': relative_path,
                    'language': result.language,
                    **chunk['metadata']
                })
                ids.append(chunk_id)
            
            self.vector_store.add_documents(documents, metadatas, ids)
        
        # Update database record
        await self._save_indexed_file(result, relative_path, existing)
        
        return result
    
    async def _get_existing_file(self, relative_path: str) -> Optional[IndexedFile]:
        """Get existing indexed file record."""
        query = select(IndexedFile).where(
            IndexedFile.repository_id == self.repository_id,
            IndexedFile.relative_path == relative_path
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _save_indexed_file(
        self, 
        result: ParseResult, 
        relative_path: str,
        existing: Optional[IndexedFile]
    ) -> IndexedFile:
        """Save or update indexed file record."""
        if existing:
            # Update existing record
            existing.content_hash = result.content_hash
            existing.language = result.language
            existing.size_bytes = result.size_bytes
            existing.line_count = result.line_count
            existing.is_indexed = True
            existing.chunk_count = len(result.chunks)
            existing.function_count = sum(1 for e in result.entities if e.type in ('function', 'method'))
            existing.class_count = sum(1 for e in result.entities if e.type == 'class')
            record = existing
        else:
            # Create new record
            record = IndexedFile(
                repository_id=self.repository_id,
                file_path=result.file_path,
                file_name=Path(result.file_path).name,
                relative_path=relative_path,
                content_hash=result.content_hash,
                language=result.language,
                size_bytes=result.size_bytes,
                line_count=result.line_count,
                is_indexed=True,
                chunk_count=len(result.chunks),
                function_count=sum(1 for e in result.entities if e.type in ('function', 'method')),
                class_count=sum(1 for e in result.entities if e.type == 'class'),
            )
            self.db.add(record)
        
        await self.db.commit()
        return record
    
    async def _update_repo_status(self, status: str, stats: IndexingStats) -> None:
        """Update repository indexing status."""
        query = select(Repository).where(Repository.id == self.repository_id)
        result = await self.db.execute(query)
        repo = result.scalar_one_or_none()
        
        if repo:
            repo.status = status
            repo.indexed_files = stats.indexed_files
            repo.total_files = stats.total_files
            repo.languages = stats.languages if stats.languages else None
            await self.db.commit()


async def index_repository(
    repository_id: int,
    directory_path: str,
    db: AsyncSession
) -> IndexingStats:
    """Main entry point for repository indexing."""
    indexer = RepositoryIndexer(repository_id, db)
    return await indexer.index_directory(directory_path)
