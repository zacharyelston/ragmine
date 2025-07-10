"""RAGMine MCP Server - Model Context Protocol server for RAGMine."""

__version__ = '0.1.0'
__author__ = 'RAGMine Team'
__email__ = 'support@ragmine.dev'

from .server import RagmineMCPServer
from .context_manager import ContextManager

__all__ = ['RagmineMCPServer', 'ContextManager']