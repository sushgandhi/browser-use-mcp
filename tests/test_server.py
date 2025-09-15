#!/usr/bin/env python3
"""
Test script for the Document Link Extractor MCP Server.
"""

import asyncio
import json
import sys
from typing import Dict, Any

# Import from the modular structure
from extractor import DocumentLinkExtractor
from config import logging

logger = logging.getLogger(__name__)


async def test_extract_links():
    """Test the link extraction functionality."""
    print("Testing Document Link Extractor MCP Server...")
    
    # Initialize the extractor
    extractor = DocumentLinkExtractor()
    
    try:
        # Test with modelcontextprotocol.io
        print("\n1. Testing with modelcontextprotocol.io:")
        result = await extractor.extract_links("https://modelcontextprotocol.io")
        
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Found {result.get('total_links_found', 0)} document links")
            if result.get('document_links'):
                for link in result['document_links'][:3]:  # Show first 3
                    print(f"  - {link['text']}: {link['url']} ({link['file_type']})")
        
        # Test with a different site
        print("\n2. Testing with example.com:")
        result = await extractor.extract_links("https://example.com")
        
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Found {result.get('total_links_found', 0)} document links")
            if result.get('document_links'):
                for link in result['document_links'][:3]:  # Show first 3
                    print(f"  - {link['text']}: {link['url']} ({link['file_type']})")
        
        # Test with a site that likely has documents
        print("\n3. Testing with w3.org (likely to have PDFs):")
        result = await extractor.extract_links("https://www.w3.org/")
        
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Found {result.get('total_links_found', 0)} document links")
            if result.get('document_links'):
                for link in result['document_links'][:3]:  # Show first 3
                    print(f"  - {link['text']}: {link['url']} ({link['file_type']})")
        
        print("\nTest complete!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"Test failed: {e}")
    
    finally:
        # Clean up
        await extractor.cleanup()


if __name__ == '__main__':
    asyncio.run(test_extract_links())
