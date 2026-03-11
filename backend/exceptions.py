"""
Custom exceptions for PyVizAST backend

@author: Chidc
@link: github.com/chidcGithub
"""
from typing import Optional, Dict, Any


class AnalysisError(Exception):
    """Base exception for analysis errors
    
    Attributes:
        message: Human-readable error description
        error_code: Machine-readable error code for frontend handling
        details: Additional context about the error
    """
    
    def __init__(self, message: str = "An error occurred during analysis", 
                 error_code: str = "ANALYSIS_ERROR", 
                 details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        result = self.message
        if self.details:
            result += f" | Details: {self.details}"
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }


class CodeParsingError(AnalysisError):
    """Exception raised when Python code cannot be parsed
    
    Attributes:
        line_number: Line where parsing failed (if known)
        syntax_error: Original SyntaxError if available
    """
    
    def __init__(self, message: str = "Failed to parse Python code", 
                 error_code: str = "CODE_PARSING_ERROR",
                 line_number: Optional[int] = None,
                 syntax_error: Optional[SyntaxError] = None,
                 details: Optional[Dict[str, Any]] = None):
        self.line_number = line_number
        self.syntax_error = syntax_error
        
        details = details or {}
        if line_number is not None:
            details["line_number"] = line_number
        if syntax_error is not None:
            details["syntax_message"] = str(syntax_error)
        
        super().__init__(message, error_code, details)
    
    def __str__(self) -> str:
        result = self.message
        if self.line_number is not None:
            result += f" at line {self.line_number}"
        if self.syntax_error:
            result += f": {self.syntax_error}"
        return result


class CodeTooLargeError(AnalysisError):
    """Exception raised when code exceeds size limits
    
    Attributes:
        size: Actual size of the code (characters or lines)
        max_size: Maximum allowed size
        size_type: Type of size measurement ('characters' or 'lines')
    """
    
    def __init__(self, message: str = "Code exceeds maximum allowed size", 
                 error_code: str = "CODE_TOO_LARGE",
                 size: Optional[int] = None,
                 max_size: Optional[int] = None,
                 size_type: str = "characters",
                 details: Optional[Dict[str, Any]] = None):
        self.size = size
        self.max_size = max_size
        self.size_type = size_type
        
        details = details or {}
        if size is not None:
            details["actual_size"] = size
        if max_size is not None:
            details["max_allowed_size"] = max_size
        details["size_type"] = size_type
        
        super().__init__(message, error_code, details)
    
    def __str__(self) -> str:
        result = self.message
        if self.size is not None and self.max_size is not None:
            result += f": {self.size} {self.size_type} (max: {self.max_size})"
        return result


class ResourceNotFoundError(Exception):
    """Exception raised when a requested resource is not found
    
    Attributes:
        resource_type: Type of the resource (e.g., 'file', 'challenge', 'task')
        resource_id: Identifier of the missing resource
    """
    
    def __init__(self, message: str = "Requested resource not found",
                 resource_type: Optional[str] = None,
                 resource_id: Optional[str] = None):
        self.message = message
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(self.message)
    
    def __str__(self) -> str:
        result = self.message
        if self.resource_type:
            result = f"{self.resource_type.capitalize()} not found"
        if self.resource_id:
            result += f": {self.resource_id}"
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response"""
        return {
            "error_code": "RESOURCE_NOT_FOUND",
            "message": str(self),
            "resource_type": self.resource_type,
            "resource_id": self.resource_id
        }
