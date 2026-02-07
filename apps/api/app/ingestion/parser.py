"""
Tree-sitter based AST parser for extracting code structure.
Supports Python, JavaScript, and TypeScript.
"""
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

# Language detection by file extension
LANGUAGE_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.mjs': 'javascript',
    '.cjs': 'javascript',
}

# Try to import tree-sitter, gracefully handle if not available
try:
    import tree_sitter_python
    import tree_sitter_javascript
    import tree_sitter_typescript
    from tree_sitter import Language, Parser
    
    # Initialize languages
    PY_LANGUAGE = Language(tree_sitter_python.language())
    JS_LANGUAGE = Language(tree_sitter_javascript.language())
    TS_LANGUAGE = Language(tree_sitter_typescript.language_typescript())
    TSX_LANGUAGE = Language(tree_sitter_typescript.language_tsx())
    
    LANGUAGES = {
        'python': PY_LANGUAGE,
        'javascript': JS_LANGUAGE,
        'typescript': TS_LANGUAGE,
        'tsx': TSX_LANGUAGE,
    }
    
    TREE_SITTER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Tree-sitter not fully available: {e}")
    TREE_SITTER_AVAILABLE = False
    LANGUAGES = {}


@dataclass
class CodeEntity:
    """Represents a code entity (function, class, etc.)."""
    name: str
    type: str  # function, class, method, variable
    start_line: int
    end_line: int
    signature: str = ""
    docstring: str = ""
    parent: Optional[str] = None


@dataclass
class ParseResult:
    """Result from parsing a file."""
    file_path: str
    language: str
    content_hash: str
    size_bytes: int
    line_count: int
    entities: List[CodeEntity] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    chunks: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None


def compute_file_hash(content: bytes) -> str:
    """Compute SHA-256 hash of file content for fingerprinting."""
    return hashlib.sha256(content).hexdigest()


def detect_language(file_path: str) -> Optional[str]:
    """Detect programming language from file extension."""
    ext = Path(file_path).suffix.lower()
    return LANGUAGE_MAP.get(ext)


class CodeParser:
    """Tree-sitter based code parser for extracting AST information."""
    
    def __init__(self):
        self.parsers: Dict[str, Any] = {}
        if TREE_SITTER_AVAILABLE:
            for lang_name, language in LANGUAGES.items():
                parser = Parser(language)
                self.parsers[lang_name] = parser
    
    def parse_file(self, file_path: str) -> ParseResult:
        """Parse a single file and extract code structure."""
        path = Path(file_path)
        
        if not path.exists():
            return ParseResult(
                file_path=file_path,
                language="unknown",
                content_hash="",
                size_bytes=0,
                line_count=0,
                error=f"File not found: {file_path}"
            )
        
        # Read file content
        try:
            content = path.read_bytes()
            content_str = content.decode('utf-8', errors='replace')
        except Exception as e:
            return ParseResult(
                file_path=file_path,
                language="unknown",
                content_hash="",
                size_bytes=0,
                line_count=0,
                error=f"Failed to read file: {e}"
            )
        
        # Compute hash and basic stats
        content_hash = compute_file_hash(content)
        lines = content_str.split('\n')
        line_count = len(lines)
        size_bytes = len(content)
        
        # Detect language
        language = detect_language(file_path) or "unknown"
        
        result = ParseResult(
            file_path=file_path,
            language=language,
            content_hash=content_hash,
            size_bytes=size_bytes,
            line_count=line_count,
        )
        
        # Parse with tree-sitter if available
        if TREE_SITTER_AVAILABLE and language in self.parsers:
            try:
                result.entities = self._extract_entities(content, language)
                result.imports = self._extract_imports(content, language)
            except Exception as e:
                logger.warning(f"Tree-sitter parsing failed for {file_path}: {e}")
        
        # Create chunks for indexing
        result.chunks = self._create_chunks(content_str, result.entities, file_path)
        
        return result
    
    def _extract_entities(self, content: bytes, language: str) -> List[CodeEntity]:
        """Extract code entities (functions, classes) from AST."""
        entities = []
        parser = self.parsers.get(language)
        if not parser:
            return entities
        
        tree = parser.parse(content)
        root = tree.root_node
        
        # Query patterns based on language
        if language == 'python':
            entities.extend(self._extract_python_entities(root, content))
        elif language in ('javascript', 'typescript', 'tsx'):
            entities.extend(self._extract_js_entities(root, content))
        
        return entities
    
    def _extract_python_entities(self, root, content: bytes) -> List[CodeEntity]:
        """Extract entities from Python AST."""
        entities = []
        
        def traverse(node, parent_name=None):
            if node.type == 'function_definition':
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = content[name_node.start_byte:name_node.end_byte].decode()
                    # Get signature
                    params_node = node.child_by_field_name('parameters')
                    params = content[params_node.start_byte:params_node.end_byte].decode() if params_node else "()"
                    
                    entities.append(CodeEntity(
                        name=name,
                        type='method' if parent_name else 'function',
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        signature=f"def {name}{params}",
                        parent=parent_name
                    ))
            
            elif node.type == 'class_definition':
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = content[name_node.start_byte:name_node.end_byte].decode()
                    entities.append(CodeEntity(
                        name=name,
                        type='class',
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        signature=f"class {name}"
                    ))
                    
                    # Traverse class body for methods
                    body = node.child_by_field_name('body')
                    if body:
                        for child in body.children:
                            traverse(child, name)
                    return  # Don't traverse children again
            
            for child in node.children:
                traverse(child, parent_name)
        
        traverse(root)
        return entities
    
    def _extract_js_entities(self, root, content: bytes) -> List[CodeEntity]:
        """Extract entities from JavaScript/TypeScript AST."""
        entities = []
        
        def traverse(node, parent_name=None):
            # Function declarations
            if node.type in ('function_declaration', 'method_definition', 'arrow_function'):
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = content[name_node.start_byte:name_node.end_byte].decode()
                    entities.append(CodeEntity(
                        name=name,
                        type='function',
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        signature=f"function {name}()",
                        parent=parent_name
                    ))
            
            # Class declarations
            elif node.type == 'class_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = content[name_node.start_byte:name_node.end_byte].decode()
                    entities.append(CodeEntity(
                        name=name,
                        type='class',
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        signature=f"class {name}"
                    ))
                    
                    body = node.child_by_field_name('body')
                    if body:
                        for child in body.children:
                            traverse(child, name)
                    return
            
            for child in node.children:
                traverse(child, parent_name)
        
        traverse(root)
        return entities
    
    def _extract_imports(self, content: bytes, language: str) -> List[str]:
        """Extract import statements from code."""
        imports = []
        parser = self.parsers.get(language)
        if not parser:
            return imports
        
        tree = parser.parse(content)
        root = tree.root_node
        
        def traverse(node):
            if node.type in ('import_statement', 'import_from_statement', 'import_declaration'):
                imports.append(content[node.start_byte:node.end_byte].decode())
            for child in node.children:
                traverse(child)
        
        traverse(root)
        return imports
    
    def _create_chunks(
        self, 
        content: str, 
        entities: List[CodeEntity], 
        file_path: str,
        chunk_size: int = 1500,
        chunk_overlap: int = 200
    ) -> List[Dict[str, Any]]:
        """Create text chunks for vector indexing."""
        chunks = []
        lines = content.split('\n')
        
        # If we have entities, chunk by entity
        if entities:
            for entity in entities:
                entity_content = '\n'.join(lines[entity.start_line - 1:entity.end_line])
                chunks.append({
                    'content': entity_content,
                    'metadata': {
                        'file_path': file_path,
                        'entity_name': entity.name,
                        'entity_type': entity.type,
                        'start_line': entity.start_line,
                        'end_line': entity.end_line,
                        'signature': entity.signature,
                    }
                })
        
        # Also create overlapping chunks for full file coverage
        current_chunk = []
        current_size = 0
        chunk_start = 0
        
        for i, line in enumerate(lines):
            current_chunk.append(line)
            current_size += len(line) + 1
            
            if current_size >= chunk_size:
                chunk_content = '\n'.join(current_chunk)
                chunks.append({
                    'content': chunk_content,
                    'metadata': {
                        'file_path': file_path,
                        'chunk_type': 'sliding_window',
                        'start_line': chunk_start + 1,
                        'end_line': i + 1,
                    }
                })
                
                # Keep overlap
                overlap_lines = int(chunk_overlap / 50)  # Approximate lines for overlap
                current_chunk = current_chunk[-overlap_lines:] if overlap_lines > 0 else []
                current_size = sum(len(l) + 1 for l in current_chunk)
                chunk_start = max(0, i - overlap_lines + 1)
        
        # Add remaining content
        if current_chunk:
            chunks.append({
                'content': '\n'.join(current_chunk),
                'metadata': {
                    'file_path': file_path,
                    'chunk_type': 'sliding_window',
                    'start_line': chunk_start + 1,
                    'end_line': len(lines),
                }
            })
        
        return chunks


# Singleton instance
_parser = None

def get_parser() -> CodeParser:
    """Get singleton parser instance."""
    global _parser
    if _parser is None:
        _parser = CodeParser()
    return _parser
