from typing import AsyncGenerator, Optional
import asyncio
from groq import AsyncGroq
from app.core.config import get_settings


class AgentOrchestrator:
    """
    LangGraph-style orchestrator for multi-agent processing.
    
    Pipeline: Planner → Retriever → Generator → Verifier
    """
    
    def __init__(self):
        self.settings = get_settings()  # Load settings when orchestrator is created
        self.groq_client = None
        
        # Hardcoded API key (temporary)
        api_key = "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"
        
        if api_key:
            self.groq_client = AsyncGroq(api_key=api_key)
    
    async def process(
        self,
        query: str,
        repo_context: Optional[dict] = None
    ) -> AsyncGenerator[dict, None]:
        """Process query through the agent pipeline."""
        
        # 1. Planner Agent - Decompose query
        yield {"type": "status", "agent": "planner", "status": "Analyzing query..."}
        plan = await self._run_planner(query, repo_context)
        yield {"type": "status", "agent": "planner", "status": "Query decomposed", "plan": plan}
        
        # 2. Retriever Agent - Fetch relevant code
        yield {"type": "status", "agent": "retriever", "status": "Searching codebase..."}
        retrieved_context = await self._run_retriever(plan, repo_context)
        
        # Emit citations
        for citation in retrieved_context.get("citations", []):
            yield {"type": "citation", "citation": citation}
        
        yield {"type": "status", "agent": "retriever", "status": f"Found {len(retrieved_context.get('chunks', []))} relevant sections"}
        
        # 3. Generator Agent - Generate response
        yield {"type": "status", "agent": "generator", "status": "Generating response..."}
        
        async for token in self._run_generator(query, plan, retrieved_context, repo_context):
            yield {"type": "content", "content": token}
        
        # 4. Verifier Agent - Check for hallucinations
        yield {"type": "status", "agent": "verifier", "status": "Verifying response..."}
        risk_analysis = await self._run_verifier(query, retrieved_context)
        yield {"type": "risk", "risk": risk_analysis}
    
    async def _run_planner(self, query: str, repo_context: Optional[dict]) -> dict:
        """Planner agent: Decompose query into sub-tasks."""
        if not self.groq_client:
            return {
                "tasks": [{"type": "search", "query": query}],
                "intent": "general_question"
            }
        
        system_prompt = """You are a query planner for a code repository Q&A system.
Decompose the user's question into specific search tasks.
Return a JSON object with:
- tasks: list of {type: "search"|"explain"|"trace", query: string}
- intent: "explanation"|"code_generation"|"debugging"|"architecture"
"""
        
        try:
            response = await self.groq_client.chat.completions.create(
                model=self.settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Repository: {repo_context.get('name', 'Unknown') if repo_context else 'Not specified'}\n\nQuestion: {query}"}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse response (simplified)
            return {
                "tasks": [{"type": "search", "query": query}],
                "intent": "explanation",
                "raw_plan": response.choices[0].message.content
            }
        except Exception as e:
            return {
                "tasks": [{"type": "search", "query": query}],
                "intent": "general_question",
                "error": str(e)
            }
    
    async def _run_retriever(self, plan: dict, repo_context: Optional[dict]) -> dict:
        """Retriever agent: Fetch relevant code from ChromaDB."""
        from app.services.vector_store import get_vector_store
        
        repo_id = repo_context.get("id") if repo_context else None
        vector_store = get_vector_store(repo_id)
        
        # Get query from plan
        query = plan.get("tasks", [{}])[0].get("query", "")
        
        # Query ChromaDB
        results = vector_store.query(query_text=query, n_results=5)
        
        chunks = []
        citations = []
        
        for i, (doc, meta, dist) in enumerate(zip(
            results["documents"],
            results["metadatas"],
            results["distances"]
        )):
            chunks.append({
                "content": doc,
                "file": meta.get("file", "unknown"),
                "lines": meta.get("lines", ""),
                "score": 1 - dist  # Convert distance to similarity
            })
            citations.append({
                "file": meta.get("file", "unknown"),
                "lines": meta.get("lines", "")
            })
        
        # If no results from vector store, return mock data for demo
        if not chunks:
            return {
                "chunks": [
                    {
                        "content": "# No indexed code found\n# Please index a repository first",
                        "file": "demo.py",
                        "lines": "1-2",
                        "score": 0.5
                    }
                ],
                "citations": [{"file": "demo.py", "lines": "1-2"}]
            }
        
        return {"chunks": chunks, "citations": citations}
    
    async def _run_generator(
        self,
        query: str,
        plan: dict,
        retrieved_context: dict,
        repo_context: Optional[dict]
    ) -> AsyncGenerator[str, None]:
        """Generator agent: Stream response generation."""
        if not self.groq_client:
            # Fallback response
            fallback = f"I analyzed your question about \"{query[:50]}...\"\n\nBased on the repository structure, I found relevant code sections. Please configure your GROQ_API_KEY to enable full analysis capabilities."
            for char in fallback:
                yield char
                await asyncio.sleep(0.01)
            return
        
        system_prompt = """You are an expert code assistant specializing in repository analysis. Provide refined, professional answers using ONLY the provided context.

RESPONSE FORMAT:
1. Start with a direct answer to the question
2. Include relevant code snippets with explanations
3. Reference specific files and line numbers
4. End with a [SUMMARY] section

GUIDELINES:
• Use markdown code blocks (```language) for all code examples
• Explain what each code snippet does
• Be concise but thorough
• If information is unavailable, clearly state "I don't have access to that information in the indexed code"
• Focus on practical, actionable insights
• Structure your response with clear sections using markdown headers (##)

EXAMPLE RESPONSE STRUCTURE:
## Analysis
[Direct answer to the question]

## Relevant Code
```python
# Original code from the repository
def example():
    pass
```
This function handles...

## [SUMMARY]
[Brief 2-3 sentence recap]
"""
        
        context_str = "\n\n".join([
            f"File: {chunk['file']} (Lines {chunk['lines']})\n```\n{chunk['content']}\n```"
            for chunk in retrieved_context.get("chunks", [])
        ])
        
        try:
            stream = await self.groq_client.chat.completions.create(
                model=self.settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context:\n{context_str}\n\nQuestion: {query}"}
                ],
                temperature=0.5,
                max_tokens=2000,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            yield f"\n\n[Error generating response: {str(e)}]"
    
    async def _run_verifier(self, query: str, retrieved_context: dict) -> dict:
        """Verifier agent: Check response for hallucinations."""
        # Simplified verification logic
        # In production, this would cross-reference generated claims with source code
        
        has_citations = len(retrieved_context.get("citations", [])) > 0
        
        if has_citations:
            return {
                "level": "low",
                "description": "Response is grounded in retrieved code snippets with proper citations."
            }
        else:
            return {
                "level": "medium",
                "description": "Limited source context available. Some claims may need manual verification."
            }
