"""
Git operations service for cloning and managing repositories.
"""
import os
import re
import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from git import Repo, GitCommandError
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class GitServiceError(Exception):
    """Base exception for git service errors."""
    pass


class GitService:
    """Service for handling git operations."""
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize Git Service.
        
        Args:
            base_dir: Base directory for cloned repositories.
                     Defaults to settings.CLONE_BASE_DIR
        """
        self.base_dir = Path(base_dir or settings.CLONE_BASE_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def is_valid_git_url(self, url: str) -> bool:
        """
        Validate if a string is a valid git URL.
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid git URL, False otherwise
        """
        if not url:
            return False
        
        # Patterns for common git URL formats
        patterns = [
            r'^https?://[^/]+/[\w\-]+/[\w\-]+\.git$',  # HTTPS with .git
            r'^https?://[^/]+/[\w\-]+/[\w\-]+/?$',      # HTTPS without .git
            r'^git@[^:]+:[\w\-]+/[\w\-]+\.git$',        # SSH format
            r'^ssh://git@[^/]+/[\w\-]+/[\w\-]+\.git$',  # SSH with protocol
        ]
        
        return any(re.match(pattern, url) for pattern in patterns)
    
    def get_repo_name_from_url(self, url: str) -> str:
        """
        Extract repository name from git URL.
        
        Args:
            url: Git repository URL
            
        Returns:
            Repository name
            
        Raises:
            GitServiceError: If URL is invalid
        """
        if not url:
            raise GitServiceError("Empty URL provided")
        
        # Extract from various formats
        # https://github.com/user/repo.git -> repo
        # git@github.com:user/repo.git -> repo
        
        # Remove .git suffix if present
        url_clean = url.rstrip('/').replace('.git', '')
        
        # Extract last part as repo name
        parts = url_clean.split('/')
        if len(parts) >= 1:
            return parts[-1]
        
        # Fallback for SSH format
        if ':' in url_clean:
            parts = url_clean.split(':')[-1].split('/')
            if parts:
                return parts[-1]
        
        raise GitServiceError(f"Could not extract repository name from URL: {url}")
    
    def get_clone_path(self, user_id: int, repo_name: str) -> Path:
        """
        Get the path where a repository should be cloned.
        
        Args:
            user_id: User ID
            repo_name: Repository name
            
        Returns:
            Path object for clone destination
        """
        return self.base_dir / str(user_id) / repo_name
    
    def clone_repository(
        self, 
        url: str, 
        user_id: int,
        repo_name: Optional[str] = None,
        depth: Optional[int] = None
    ) -> Path:
        """
        Clone a git repository.
        
        Args:
            url: Git repository URL
            user_id: User ID for organizing cloned repos
            repo_name: Optional custom repository name
            depth: Optional clone depth for shallow clone
            
        Returns:
            Path to cloned repository
            
        Raises:
            GitServiceError: If cloning fails
        """
        # Validate URL
        if not self.is_valid_git_url(url):
            raise GitServiceError(f"Invalid git URL: {url}")
        
        # Get repo name
        if not repo_name:
            repo_name = self.get_repo_name_from_url(url)
        
        # Get destination path
        destination = self.get_clone_path(user_id, repo_name)
        
        # Remove existing directory if it exists
        if destination.exists():
            logger.warning(f"Destination already exists, removing: {destination}")
            import shutil
            shutil.rmtree(destination)
        
        # Create parent directory
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            logger.info(f"Cloning {url} to {destination}")
            
            # Clone with optional depth for faster cloning
            clone_kwargs = {'depth': depth} if depth else {}
            Repo.clone_from(url, destination, **clone_kwargs)
            
            logger.info(f"Successfully cloned repository to {destination}")
            return destination
            
        except GitCommandError as e:
            error_msg = f"Failed to clone repository: {e}"
            logger.error(error_msg)
            
            # Clean up failed clone
            if destination.exists():
                import shutil
                shutil.rmtree(destination)
            
            raise GitServiceError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during clone: {e}"
            logger.error(error_msg)
            raise GitServiceError(error_msg)
    
    def pull_latest(self, repo_path: Path) -> bool:
        """
        Pull latest changes from remote repository.
        
        Args:
            repo_path: Path to local repository
            
        Returns:
            True if successful, False otherwise
        """
        try:
            repo = Repo(repo_path)
            origin = repo.remotes.origin
            origin.pull()
            logger.info(f"Successfully pulled latest changes for {repo_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to pull latest changes: {e}")
            return False
    
    def get_repository_info(self, repo_path: Path) -> dict:
        """
        Get information about a cloned repository.
        
        Args:
            repo_path: Path to repository
            
        Returns:
            Dictionary with repository information
        """
        try:
            repo = Repo(repo_path)
            
            return {
                'is_valid': True,
                'current_branch': repo.active_branch.name,
                'remote_url': next(repo.remotes.origin.urls, None),
                'commit_count': len(list(repo.iter_commits())),
                'latest_commit': {
                    'sha': repo.head.commit.hexsha,
                    'message': repo.head.commit.message,
                    'author': str(repo.head.commit.author),
                    'date': repo.head.commit.committed_datetime.isoformat(),
                }
            }
        except Exception as e:
            logger.error(f"Error getting repository info: {e}")
            return {'is_valid': False, 'error': str(e)}


# Singleton instance
_git_service: Optional[GitService] = None


def get_git_service() -> GitService:
    """Get singleton GitService instance."""
    global _git_service
    if _git_service is None:
        _git_service = GitService()
    return _git_service
