"""
AST Node Styles - Define node appearance and constants

@author: Chidc
@link: github.com/chidcGithub
"""
from ..models.schemas import NodeType


# Performance optimization: Skip these node types in simplified mode
SKIP_TYPES_SIMPLIFIED = {
    'expr', 'expr_context', 'slice', 'boolop', 'operator', 
    'unaryop', 'cmpop', 'comprehension', 'excepthandler',
    'arguments', 'arg', 'keyword', 'alias', 'withitem',
    'type_ignore', 'type_param', 'pattern'
}

# Priority node types that are always kept
PRIORITY_NODE_TYPES = {
    'Module', 'FunctionDef', 'AsyncFunctionDef', 'ClassDef',
    'If', 'For', 'AsyncFor', 'While', 'Try', 'With', 'AsyncWith',
    'Import', 'ImportFrom', 'Return', 'Yield', 'YieldFrom'
}


# Mapping of node types to colors, shapes, and icons/descriptions
NODE_STYLES = {
    # Structural nodes
    NodeType.MODULE: {"color": "#ffffff", "shape": "hexagon", "size": 30, "icon": "📦", "description": "Module"},
    NodeType.FUNCTION: {"color": "#ffffff", "shape": "roundrectangle", "size": 25, "icon": "ƒ", "description": "Function"},
    NodeType.CLASS: {"color": "#e0e0e0", "shape": "roundrectangle", "size": 28, "icon": "C", "description": "Class"},
    
    # Control flow
    NodeType.IF: {"color": "#a0a0a0", "shape": "diamond", "size": 20, "icon": "?", "description": "Conditional"},
    NodeType.FOR: {"color": "#a0a0a0", "shape": "diamond", "size": 20, "icon": "⟳", "description": "For Loop"},
    NodeType.WHILE: {"color": "#a0a0a0", "shape": "diamond", "size": 20, "icon": "↻", "description": "While Loop"},
    NodeType.TRY: {"color": "#909090", "shape": "diamond", "size": 22, "icon": "⚠", "description": "Exception Handler"},
    NodeType.WITH: {"color": "#909090", "shape": "diamond", "size": 20, "icon": "▶", "description": "Context Manager"},
    NodeType.MATCH: {"color": "#a0a0a0", "shape": "diamond", "size": 22, "icon": "⬡", "description": "Match Statement"},
    
    # Expressions
    NodeType.CALL: {"color": "#707070", "shape": "circle", "size": 15, "icon": "()", "description": "Function Call"},
    NodeType.BINARY_OP: {"color": "#606060", "shape": "circle", "size": 12, "icon": "+", "description": "Binary Operation"},
    NodeType.COMPARE: {"color": "#606060", "shape": "circle", "size": 12, "icon": "≡", "description": "Comparison"},
    NodeType.LAMBDA: {"color": "#d0d0d0", "shape": "ellipse", "size": 18, "icon": "λ", "description": "Lambda Expression"},
    
    # Data structures
    NodeType.LIST: {"color": "#808080", "shape": "rectangle", "size": 15, "icon": "[]", "description": "List"},
    NodeType.DICT: {"color": "#808080", "shape": "rectangle", "size": 15, "icon": "{}", "description": "Dictionary"},
    NodeType.SET: {"color": "#808080", "shape": "rectangle", "size": 15, "icon": "∅", "description": "Set"},
    NodeType.TUPLE: {"color": "#808080", "shape": "rectangle", "size": 15, "icon": "()", "description": "Tuple"},
    
    # Variables
    NodeType.ASSIGN: {"color": "#505050", "shape": "circle", "size": 14, "icon": "=", "description": "Assignment"},
    NodeType.NAME: {"color": "#404040", "shape": "circle", "size": 10, "icon": "x", "description": "Variable Name"},
    
    # Other
    NodeType.IMPORT: {"color": "#909090", "shape": "parallelogram", "size": 16, "icon": "↓", "description": "Import"},
    NodeType.RETURN: {"color": "#707070", "shape": "triangle", "size": 14, "icon": "←", "description": "Return"},
    NodeType.YIELD: {"color": "#707070", "shape": "triangle", "size": 14, "icon": "→", "description": "Yield"},
    NodeType.OTHER: {"color": "#404040", "shape": "circle", "size": 10, "icon": "•", "description": "Other"},
}
