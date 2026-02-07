from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import logging
from pathlib import Path

from app.core.database import get_db, async_session_maker
from app.core.security import get_current_user
from app.models.user import User
from app.models.repository import Repository
from app.models.indexed_file import IndexedFile
from app.schemas.chat import RepositoryCreate, RepositoryResponse
from app.ingestion.indexer import index_repository
from app.services.git_service import get_git_service, GitServiceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/repos", tags=["Repositories"])


async def clone_and_index_repository(repo_id: int, url: str, user_id: int, repo_name: str):
    """Background task to clone and index a repository."""
    async with async_session_maker() as db:
        git_service = get_git_service()
        
        try:
            # Update status to cloning
            result = await db.execute(select(Repository).where(Repository.id == repo_id))
            repo = result.scalar_one_or_none()
            if not repo:
                logger.error(f"Repository {repo_id} not found")
                return
            
            repo.status = "cloning"
            await db.commit()
            logger.info(f"Cloning repository {repo_id} from {url}")
            
            # Clone repository
            local_path = git_service.clone_repository(url, user_id, repo_name, depth=1)
            
            # Update repository with local path
            repo.local_path = str(local_path)
            repo.status = "indexing"
            await db.commit()
            logger.info(f"Successfully cloned to {local_path}, starting indexing")
            
            # Index repository
            stats = await index_repository(repo_id, str(local_path), db)
            logger.info(f"Completed indexing: {stats.indexed_files} files, {stats.total_chunks} chunks")
            
        except GitServiceError as e:
            logger.error(f"Git clone failed for repository {repo_id}: {e}")
            result = await db.execute(select(Repository).where(Repository.id == repo_id))
            repo = result.scalar_one_or_none()
            if repo:
                repo.status = "error"
                await db.commit()
        except Exception as e:
            logger.error(f"Clone/indexing failed for repository {repo_id}: {e}")
            result = await db.execute(select(Repository).where(Repository.id == repo_id))
            repo = result.scalar_one_or_none()
            if repo:
                repo.status = "error"
                await db.commit()


async def run_indexing_task(repo_id: int, local_path: str):
    """Background task to index a repository (for existing local paths)."""
    async with async_session_maker() as db:
        try:
            logger.info(f"Starting indexing for repository {repo_id}")
            stats = await index_repository(repo_id, local_path, db)
            logger.info(f"Completed indexing: {stats.indexed_files} files, {stats.total_chunks} chunks")
        except Exception as e:
            logger.error(f"Indexing failed for repository {repo_id}: {e}")
            # Update status to error
            result = await db.execute(select(Repository).where(Repository.id == repo_id))
            repo = result.scalar_one_or_none()
            if repo:
                repo.status = "error"
                await db.commit()


@router.post("/", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
async def create_repository(
    repo_data: RepositoryCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Repository:
    """Create a new repository and start cloning/indexing."""
    git_service = get_git_service()
    
    # Validate URL if provided
    if repo_data.url and not git_service.is_valid_git_url(repo_data.url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid git URL format: {repo_data.url}"
        )
    
    repo = Repository(
        name=repo_data.name,
        description=repo_data.description,
        url=repo_data.url,
        local_path=repo_data.local_path,
        user_id=current_user.id,
        status="pending"
    )
    db.add(repo)
    await db.commit()
    await db.refresh(repo)
    
    # Determine workflow: Clone + Index OR Direct Index
    if repo.url and not repo.local_path:
        # Clone from URL, then index
        logger.info(f"Triggering clone and index for repo {repo.id} from {repo.url}")
        background_tasks.add_task(
            clone_and_index_repository, 
            repo.id, 
            repo.url, 
            current_user.id,
            repo.name
        )
        repo.status = "cloning"
        await db.commit()
    elif repo.local_path:
        # Direct indexing from local path
        logger.info(f"Triggering direct indexing for repo {repo.id} from {repo.local_path}")
        background_tasks.add_task(run_indexing_task, repo.id, repo.local_path)
        repo.status = "indexing"
        await db.commit()
    else:
        # No URL and no local path - just save as pending
        logger.warning(f"Repository {repo.id} created without URL or local_path")
    
    return repo


@router.get("/", response_model=List[RepositoryResponse])
async def list_repositories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Repository]:
    """List user's repositories."""
    result = await db.execute(
        select(Repository)
        .where(Repository.user_id == current_user.id)
        .order_by(Repository.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{repo_id}", response_model=RepositoryResponse)
async def get_repository(
    repo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Repository:
    """Get a specific repository."""
    result = await db.execute(
        select(Repository)
        .where(Repository.id == repo_id)
        .where(Repository.user_id == current_user.id)
    )
    repo = result.scalar_one_or_none()
    
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    return repo


@router.delete("/{repo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repository(
    repo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a repository."""
    result = await db.execute(
        select(Repository)
        .where(Repository.id == repo_id)
        .where(Repository.user_id == current_user.id)
    )
    repo = result.scalar_one_or_none()
    
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    await db.delete(repo)
    await db.commit()


@router.post("/{repo_id}/reindex", response_model=RepositoryResponse)
async def reindex_repository(
    repo_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Repository:
    """Trigger re-indexing of a repository."""
    result = await db.execute(
        select(Repository)
        .where(Repository.id == repo_id)
        .where(Repository.user_id == current_user.id)
    )
    repo = result.scalar_one_or_none()
    
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    if not repo.local_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository has no local path to index"
        )
    
    repo.status = "indexing"
    await db.commit()
    await db.refresh(repo)
    
    # Start background indexing task
    background_tasks.add_task(run_indexing_task, repo.id, repo.local_path)
    
    return repo


@router.get("/{repo_id}/structure")
async def get_repository_structure(
    repo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get repository file structure for visualization."""
    # Verify repo ownership
    result = await db.execute(
        select(Repository)
        .where(Repository.id == repo_id)
        .where(Repository.user_id == current_user.id)
    )
    repo = result.scalar_one_or_none()
    
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    # Get all indexed files for this repo
    files_result = await db.execute(
        select(IndexedFile)
        .where(IndexedFile.repository_id == repo_id)
        .order_by(IndexedFile.relative_path)
    )
    files = files_result.scalars().all()
    
    # Build tree structure
    tree = _build_tree(files)
    
    return {
        "repository": repo.name,
        "total_files": len(files),
        "tree": tree
    }


def _build_tree(files: List[IndexedFile]) -> dict:
    """Build a tree structure from flat file list."""
    tree = {"name": "root", "type": "folder", "path": "/", "children": []}
    
    for file in files:
        parts = file.relative_path.replace("\\", "/").split("/")
        current = tree
        
        # Navigate/create folder structure
        for i, part in enumerate(parts[:-1]):
            found = None
            for child in current.get("children", []):
                if child["name"] == part and child["type"] == "folder":
                    found = child
                    break
            
            if not found:
                found = {
                    "name": part,
                    "type": "folder",
                    "path": "/".join(parts[:i+1]),
                    "children": []
                }
                current["children"].append(found)
            
            current = found
        
        # Add file
        current["children"].append({
            "name": file.file_name,
            "type": "file",
            "path": file.relative_path,
            "size": file.size_bytes,
            "language": file.language,
            "line_count": file.line_count,
            "is_indexed": file.is_indexed
        })
    
    return tree

