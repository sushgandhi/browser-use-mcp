#!/usr/bin/env python3
"""
MCP Server for extracting document download links from websites.

This server provides a simple tool to navigate to any website
and extract document download links without actually downloading anything.
The links are returned as structured data for use in other systems.
"""

import asyncio
import json
import sys
from typing import Any

# Import all dependencies at the top
from fastmcp import FastMCP

from config import logging
from extractor import DocumentLinkExtractor
from generic_intelligent_extractor import EnhancedGenericFinder

logger = logging.getLogger(__name__)


# Initialize FastMCP server directly
mcp = FastMCP("document-link-extractor", version="2.0.0")

# Global server instances
extractor = DocumentLinkExtractor()
intelligent_finder = EnhancedGenericFinder(include_cost=True)


@mcp.tool()
async def get_document_download_links(url: str) -> str:
    """
    Navigate to a website and extract document download links.
    
    This tool navigates to any website and extracts document download links
    (PDF, Excel, Word, etc.). It returns structured data about available downloads
    without actually downloading any files.
    
    Args:
        url: The URL to navigate to (e.g., 'https://modelcontextprotocol.io')
    
    Returns:
        A JSON string containing extracted download links with metadata:
        - Link text and URL
        - File type (PDF, Excel, Word, etc.)
        - Document category if detectable
        - Source website
    """
    logger.info(f"Extracting document download links from: {url}")
    
    try:
        result = await extractor.extract_links(url)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error extracting document links: {e}", exc_info=True)
        error_result = {
            'error': str(e),
            'message': 'Failed to extract document download links. The website may be unavailable or require authentication.',
            'suggestion': 'Try accessing the page manually first to verify it contains downloadable documents.'
        }
        return json.dumps(error_result, indent=2)


@mcp.tool()
async def extract_modelcontextprotocol_links() -> str:
    """
    Specialized tool to extract document links from modelcontextprotocol.io.
    
    This is a convenience tool that automatically navigates to modelcontextprotocol.io
    and extracts any document download links available on the site.
    
    Returns:
        A JSON string containing document download links from modelcontextprotocol.io
    """
    logger.info("Extracting document links from modelcontextprotocol.io")
    return await get_document_download_links("https://modelcontextprotocol.io")


@mcp.tool()
async def find_documents_intelligent(website_url: str, search_query: str) -> str:
    """
    Intelligently find any type of documents from a website using AI-powered navigation.
    
    This tool uses browser-use's agent capabilities to:
    1. Navigate to the website and understand its structure
    2. Search for content matching your query
    3. Find direct links to relevant documents, articles, PDFs, or downloadable content
    4. Extract the direct URLs to the documents
    5. Capture titles, descriptions, and any available metadata
    
    Args:
        website_url: The website URL to search (e.g., 'finance.yahoo.com' or 'https://finance.yahoo.com')
        search_query: What to search for (e.g., 'JPMorgan latest news PDF', 'annual reports', 'quarterly earnings')
    
    Returns:
        A JSON string containing found documents with:
        - Document titles and direct URLs
        - Document types (PDF, Article, News, Report, etc.)
        - Descriptions and dates if available
        - Search summary of what was found
        - Token usage statistics including cost estimates
    """
    logger.info(f"Intelligently searching for '{search_query}' at: {website_url}")
    
    try:
        result = await intelligent_finder.find_documents(website_url, search_query)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error finding documents: {e}", exc_info=True)
        error_result = {
            'success': False,
            'error': str(e),
            'search_summary': f'Failed to find documents: {str(e)}',
            'token_usage': {
                'total_tokens': 0,
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'total_cost': 0.0,
                'model': 'gpt-4o-mini',
                'entry_count': 0
            }
        }
        return json.dumps(error_result, indent=2)


@mcp.tool()
async def find_pdf_documents(website_url: str, topic: str) -> str:
    """
    Find PDF documents on a specific topic from a website using intelligent navigation.
    
    This tool navigates to a website and uses AI to:
    1. Search for PDF files related to your topic
    2. Look for download links and document sections
    3. Find direct URLs to PDF documents
    4. Extract document titles, descriptions, and dates
    
    Args:
        website_url: The website URL to search (e.g., 'finance.yahoo.com')
        topic: Topic to search for (e.g., 'JPMorgan', 'artificial intelligence', 'quarterly reports')
    
    Returns:
        A JSON string containing found PDF documents with:
        - Document titles and direct URLs
        - Document types and descriptions
        - Search summary of navigation results
        - Token usage statistics including cost estimates
    """
    logger.info(f"Searching for PDF documents about '{topic}' at: {website_url}")
    
    try:
        result = await intelligent_finder.find_pdf_urls(website_url, topic)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error finding PDF documents: {e}", exc_info=True)
        error_result = {
            'success': False,
            'error': str(e),
            'search_summary': f'Failed to find PDF documents: {str(e)}',
            'token_usage': {
                'total_tokens': 0,
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'total_cost': 0.0,
                'model': 'gpt-4o-mini',
                'entry_count': 0
            }
        }
        return json.dumps(error_result, indent=2)


@mcp.tool()
async def find_latest_news_pdf(website_url: str, company_name: str) -> str:
    """
    Find the latest news in PDF format for a specific company using intelligent navigation.
    
    This tool navigates to a website and uses AI to:
    1. Search for recent news articles about the company
    2. Look for PDF versions of news articles or press releases
    3. Check if articles have PDF download options
    4. Find direct links to PDF versions of the news
    
    Args:
        website_url: The website URL to search (e.g., 'finance.yahoo.com')
        company_name: Company name to search for (e.g., 'JPMorgan', 'Apple', 'Microsoft')
    
    Returns:
        A JSON string containing found news articles with:
        - Article titles and direct PDF URLs
        - Publication dates and descriptions
        - Search summary of navigation results
        - Token usage statistics including cost estimates
    """
    logger.info(f"Searching for latest PDF news about '{company_name}' at: {website_url}")
    
    try:
        result = await intelligent_finder.find_news_pdf_urls(website_url, company_name)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error finding news PDFs: {e}", exc_info=True)
        error_result = {
            'success': False,
            'error': str(e),
            'search_summary': f'Failed to find news PDFs: {str(e)}',
            'token_usage': {
                'total_tokens': 0,
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'total_cost': 0.0,
                'model': 'gpt-4o-mini',
                'entry_count': 0
            }
        }
        return json.dumps(error_result, indent=2)


@mcp.tool()
async def find_annual_reports(company_url: str) -> str:
    """
    Find annual reports from a company website using intelligent navigation.
    
    This tool navigates to a company website and uses AI to:
    1. Look for investor relations or about us sections
    2. Search for annual reports, financial reports, or yearly summaries
    3. Find direct links to report PDFs or downloadable documents
    4. Extract report titles, years, and descriptions
    
    Args:
        company_url: The company website URL (e.g., 'microsoft.com')
    
    Returns:
        A JSON string containing found annual reports with:
        - Report titles and direct URLs
        - Report years and descriptions
        - Search summary of navigation results
        - Token usage statistics including cost estimates
    """
    logger.info(f"Searching for annual reports at: {company_url}")
    
    try:
        result = await intelligent_finder.find_annual_report_urls(company_url)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error finding annual reports: {e}", exc_info=True)
        error_result = {
            'success': False,
            'error': str(e),
            'search_summary': f'Failed to find annual reports: {str(e)}',
            'token_usage': {
                'total_tokens': 0,
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'total_cost': 0.0,
                'model': 'gpt-4o-mini',
                'entry_count': 0
            }
        }
        return json.dumps(error_result, indent=2)


@mcp.tool()
async def close_browser() -> str:
    """Close the browser session and clean up resources."""
    await extractor.cleanup()
    return "Browser session closed successfully"


def main() -> int:
    """Run the MCP server."""
    try:
        # Run the server with stdio transport
        logger.info("Starting Document Link Extractor MCP Server...")
        mcp.run(transport='stdio')
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        return 1
    finally:
        # Clean up
        asyncio.run(extractor.cleanup())
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
