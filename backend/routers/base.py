"""
Base API routes (root, health check)

@author: Chidc
@link: github.com/chidcGithub
"""
from fastapi import APIRouter

router = APIRouter(tags=["base"])


@router.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "PyVizAST API",
        "version": "0.6.3",
        "description": "Python AST Visualizer and Static Analyzer",
        "status": "running",
        "endpoints": {
            "analyze": "/api/analyze",
            "ast": "/api/ast",
            "complexity": "/api/complexity",
            "performance": "/api/performance",
            "security": "/api/security",
            "suggestions": "/api/suggestions",
            "docs": "/docs"
        }
    }


@router.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "PyVizAST API"}
