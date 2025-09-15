"""Configuration and constants for the Document Link Extractor MCP Server."""

from loguru import logger
import sys

# Configure loguru for MCP compliance
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
    level="INFO"
)

# Supported document file types
DOCUMENT_FILE_TYPES = [
    '.pdf', '.xlsx', '.csv', '.doc', '.docx', '.zip', '.txt', '.ppt', '.pptx'
]

# Document keywords for detection
DOCUMENT_KEYWORDS = ['download', 'document', 'file', 'report', 'data', 'export', 'save']

# Document categories
DOCUMENT_CATEGORIES = {
    'report': ['report', 'analysis', 'study'],
    'data': ['data', 'export', 'csv'],
    'documentation': ['guide', 'manual', 'doc']
}
