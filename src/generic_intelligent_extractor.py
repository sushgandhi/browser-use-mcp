"""Enhanced generic intelligent document finder using browser-use agent capabilities."""

import asyncio
import json
import re
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

from browser_use import Agent, BrowserSession, BrowserProfile
from browser_use.llm.openai.chat import ChatOpenAI
from browser_use.tokens.service import TokenCost
from browser_use.tokens.views import UsageSummary
from pydantic import BaseModel, Field

from config import logger


class FoundDocument(BaseModel):
    """Model for a found document."""
    title: str = Field(description="Title or description of the document")
    url: str = Field(description="Direct URL to the document")
    document_type: str = Field(description="Type of document (PDF, Article, News, Report, etc.)")
    description: Optional[str] = Field(description="Additional description if available", default=None)
    date: Optional[str] = Field(description="Date if available", default=None)
    source: Optional[str] = Field(description="Source website or origin", default=None)


class GenericSearchResult(BaseModel):
    """Model for the final search results."""
    documents: List[FoundDocument] = Field(description="List of found documents")
    search_summary: str = Field(description="Summary of what was found and searched")
    success: bool = Field(description="Whether the search was successful")


class EnhancedGenericFinder:
    """Enhanced version that better leverages browser-use's system prompt for URL extraction."""
    
    def __init__(self, llm_model: str = "gpt-4o-mini", include_cost: bool = True):
        self.llm = ChatOpenAI(model=llm_model)
        self.token_cost = TokenCost(include_cost=include_cost)
        self.model_name = llm_model
        
    async def find_documents(self, website_url: str, search_query: str) -> Dict[str, Any]:
        """Find document URLs from a website using intelligent navigation."""
        logger.info(f"Starting intelligent URL search for '{search_query}' at: {website_url}")
        
        # Initialize token cost tracking
        await self.token_cost.initialize()
        
        # Register the LLM for token tracking
        tracked_llm = self.token_cost.register_llm(self.llm)
        
        # Enhanced task that leverages browser-use's system prompt capabilities
        task = f"""Navigate to {website_url} and extract URLs to documents related to: {search_query}

Your mission is to find direct URLs to downloadable content. You should:

1. First, understand the website structure and navigation
2. Look for sections like: Downloads, Documents, Reports, News, Media, Resources
3. Search for content matching: {search_query}
4. Find direct links to PDFs, documents, reports, or downloadable files
5. Extract the complete URLs - do not shorten or modify them
6. Get titles, descriptions, and available metadata
7. Return only URLs that are directly accessible

CRITICAL: You are a URL extraction specialist. Never download files. Only extract URLs.

Return the most relevant and recent document URLs found."""
        
        # Create browser profile optimized for URL discovery
        profile = BrowserProfile(
            headless=True,
            wait_between_actions=0.3,  # Faster for URL extraction
            keep_alive=True,
            disable_security=True
        )
        
        # Create browser session
        browser_session = BrowserSession(browser_profile=profile)
        
        try:
            # Create agent with enhanced system prompt for URL extraction
            agent = Agent(
                task=task,
                llm=tracked_llm,
                browser_session=browser_session,
                output_model_schema=GenericSearchResult,
                use_vision=True,
                max_steps=15,  # Reduced steps for faster URL extraction
                step_timeout=60  # Shorter timeout for URL searches
            )
            
            logger.info("Starting enhanced agent for URL extraction...")
            
            # Run the agent
            history = await agent.run(max_steps=15)
            
            # Get token usage summary
            usage_summary = await self.token_cost.get_usage_summary()
            
            # Extract the final result
            if history.structured_output:
                result = history.structured_output.model_dump()
                logger.success(f"Agent completed URL extraction successfully. Found {len(result.get('documents', []))} URLs")
                return {
                    'success': True,
                    'documents': result.get('documents', []),
                    'search_summary': result.get('search_summary', 'URL extraction completed'),
                    'agent_history': history.model_dump() if hasattr(history, 'model_dump') else str(history),
                    'token_usage': {
                        'total_tokens': usage_summary.total_tokens,
                        'prompt_tokens': usage_summary.total_prompt_tokens,
                        'completion_tokens': usage_summary.total_completion_tokens,
                        'total_cost': usage_summary.total_cost,
                        'model': self.model_name,
                        'entry_count': usage_summary.entry_count
                    }
                }
            else:
                # Try to extract information from final result
                final_result = history.final_result()
                if final_result:
                    logger.info("Extracting URLs from agent's final result")
                    return {
                        'success': True,
                        'documents': self._parse_final_result(final_result),
                        'search_summary': 'URLs extracted from agent final result',
                        'agent_history': history.model_dump() if hasattr(history, 'model_dump') else str(history),
                        'token_usage': {
                            'total_tokens': usage_summary.total_tokens,
                            'prompt_tokens': usage_summary.total_prompt_tokens,
                            'completion_tokens': usage_summary.total_completion_tokens,
                            'total_cost': usage_summary.total_cost,
                            'model': self.model_name,
                            'entry_count': usage_summary.entry_count
                        }
                    }
                else:
                    logger.warning("No structured output or final result available")
                    return {
                        'success': False,
                        'error': 'Agent completed but no URLs found',
                        'search_summary': 'Agent completed without finding document URLs',
                        'token_usage': {
                            'total_tokens': usage_summary.total_tokens,
                            'prompt_tokens': usage_summary.total_prompt_tokens,
                            'completion_tokens': usage_summary.total_completion_tokens,
                            'total_cost': usage_summary.total_cost,
                            'model': self.model_name,
                            'entry_count': usage_summary.entry_count
                        }
                    }
                    
        except Exception as e:
            logger.error(f"Error during URL extraction: {e}")
            logger.exception("Full exception details:")
            
            # Get token usage even on error
            usage_summary = await self.token_cost.get_usage_summary()
            
            return {
                'success': False,
                'error': str(e),
                'search_summary': f'URL extraction failed: {str(e)}',
                'token_usage': {
                    'total_tokens': usage_summary.total_tokens,
                    'prompt_tokens': usage_summary.total_prompt_tokens,
                    'completion_tokens': usage_summary.total_completion_tokens,
                    'total_cost': usage_summary.total_cost,
                    'model': self.model_name,
                    'entry_count': usage_summary.entry_count
                }
            }
        finally:
            # Clean up browser session
            try:
                await browser_session.stop()
            except:
                pass
    
    async def find_pdf_urls(self, website_url: str, topic: str) -> Dict[str, Any]:
        """Find PDF URLs on a specific topic from a website."""
        logger.info(f"Searching for PDF URLs about '{topic}' at: {website_url}")
        
        task = f"""Navigate to {website_url} and extract URLs to PDF documents about {topic}.

Your mission is to find direct URLs to PDF files. You should:

1. Explore the website structure efficiently
2. Search for PDF files related to {topic}
3. Look for download links, document sections, or PDF resources
4. Find complete URLs to PDF documents
5. Extract document titles, descriptions, and dates
6. Return only direct PDF URLs - no shortened or redirect URLs

CRITICAL: You are a PDF URL extraction specialist. Never download files. Only extract URLs.

Return the most relevant PDF document URLs found."""
        
        return await self._execute_enhanced_task(task, website_url, f"PDF URLs about {topic}")
    
    async def find_news_pdf_urls(self, website_url: str, company_name: str) -> Dict[str, Any]:
        """Find the latest news PDF URLs for a specific company."""
        logger.info(f"Searching for latest PDF news URLs about '{company_name}' at: {website_url}")
        
        task = f"""Navigate to {website_url} and extract URLs to PDF news about {company_name}.

Your mission is to find direct URLs to PDF news articles. You should:

1. Navigate efficiently to news sections
2. Search for recent news articles about {company_name}
3. Look for PDF versions of news articles or press releases
4. Check if articles have PDF download links
5. Find complete URLs to PDF versions of the news
6. Return only direct PDF URLs

CRITICAL: You are a news PDF URL extraction specialist. Never download files. Only extract URLs.

Return the most recent news PDF URLs found."""
        
        return await self._execute_enhanced_task(task, website_url, f"latest PDF news URLs about {company_name}")
    
    async def find_annual_report_urls(self, company_url: str) -> Dict[str, Any]:
        """Find annual report URLs from a company website."""
        logger.info(f"Searching for annual report URLs at: {company_url}")
        
        task = f"""Navigate to {company_url} and extract URLs to annual reports.

Your mission is to find direct URLs to annual report PDFs. You should:

1. Navigate efficiently to investor relations sections
2. Look for annual reports, financial reports, or yearly summaries
3. Find complete URLs to report PDFs
4. Extract report titles, years, and descriptions
5. Return only direct report URLs

CRITICAL: You are an annual report URL extraction specialist. Never download files. Only extract URLs.

Return the most recent annual report URLs found."""
        
        return await self._execute_enhanced_task(task, company_url, "annual report URLs")
    
    async def _execute_enhanced_task(self, task: str, website_url: str, search_description: str) -> Dict[str, Any]:
        """Execute an enhanced search task with better system prompt utilization."""
        # Initialize token cost tracking
        await self.token_cost.initialize()
        
        # Register the LLM for token tracking
        tracked_llm = self.token_cost.register_llm(self.llm)
        
        # Create browser profile optimized for fast URL extraction
        profile = BrowserProfile(
            headless=True,
            wait_between_actions=0.2,  # Faster for URL extraction
            keep_alive=True,
            disable_security=True
        )
        
        browser_session = BrowserSession(browser_profile=profile)
        
        try:
            # Enhanced agent with better system prompt for URL extraction
            agent = Agent(
                task=task,
                llm=tracked_llm,
                browser_session=browser_session,
                output_model_schema=GenericSearchResult,
                use_vision=True,
                max_steps=12,  # Fewer steps for faster URL extraction
                step_timeout=45  # Shorter timeout for URL searches
            )
            
            logger.info(f"Starting enhanced agent for {search_description} URL extraction...")
            history = await agent.run(max_steps=12)
            
            # Get token usage summary
            usage_summary = await self.token_cost.get_usage_summary()
            
            if history.structured_output:
                result = history.structured_output.model_dump()
                return {
                    'success': True,
                    'documents': result.get('documents', []),
                    'search_summary': result.get('search_summary', f'URL extraction completed for {search_description}'),
                    'website': website_url,
                    'search_type': search_description,
                    'token_usage': {
                        'total_tokens': usage_summary.total_tokens,
                        'prompt_tokens': usage_summary.total_prompt_tokens,
                        'completion_tokens': usage_summary.total_completion_tokens,
                        'total_cost': usage_summary.total_cost,
                        'model': self.model_name,
                        'entry_count': usage_summary.entry_count
                    }
                }
            else:
                final_result = history.final_result()
                return {
                    'success': True,
                    'documents': self._parse_final_result(final_result) if final_result else [],
                    'search_summary': f'URL extraction completed for {search_description}',
                    'website': website_url,
                    'search_type': search_description,
                    'token_usage': {
                        'total_tokens': usage_summary.total_tokens,
                        'prompt_tokens': usage_summary.total_prompt_tokens,
                        'completion_tokens': usage_summary.total_completion_tokens,
                        'total_cost': usage_summary.total_cost,
                        'model': self.model_name,
                        'entry_count': usage_summary.entry_count
                    }
                }
                    
        except Exception as e:
            logger.error(f"Error during enhanced URL extraction: {e}")
            logger.exception("Full exception details:")
            
            # Get token usage even on error
            usage_summary = await self.token_cost.get_usage_summary()
            
            return {
                'success': False,
                'error': str(e),
                'search_summary': f'URL extraction failed for {search_description}: {str(e)}',
                'website': website_url,
                'search_type': search_description,
                'token_usage': {
                    'total_tokens': usage_summary.total_tokens,
                    'prompt_tokens': usage_summary.total_prompt_tokens,
                    'completion_tokens': usage_summary.total_completion_tokens,
                    'total_cost': usage_summary.total_cost,
                    'model': self.model_name,
                    'entry_count': usage_summary.entry_count
                }
            }
        finally:
            try:
                await browser_session.stop()
            except:
                pass
    
    def _parse_final_result(self, final_result: str) -> List[Dict[str, Any]]:
        """Parse the final result text to extract document information."""
        documents = []
        
        # Look for URLs in the final result
        url_pattern = r'https?://[^\s<>"\']+\.pdf'
        urls = re.findall(url_pattern, final_result, re.IGNORECASE)
        
        for url in urls:
            # Try to extract document type from URL or surrounding text
            doc_type = "PDF"  # Default since we're looking for PDFs
            if "news" in url.lower() or "press" in url.lower():
                doc_type = "News Article"
            elif "report" in url.lower():
                doc_type = "Report"
            elif "annual" in url.lower():
                doc_type = "Annual Report"
            elif "article" in url.lower():
                doc_type = "Article"
            
            documents.append({
                'title': f'{doc_type} Document',
                'url': url,
                'document_type': doc_type,
                'description': 'Extracted from agent final result',
                'date': None,
                'source': None
            })
        
        return documents


async def main():
    """Example usage of the enhanced generic intelligent document finder."""
    finder = EnhancedGenericFinder()
    
    # Example: Find PDF URLs about AI from Yahoo Finance
    logger.info("Searching Yahoo Finance for AI-related PDF URLs...")
    result = await finder.find_pdf_urls("finance.yahoo.com", "artificial intelligence")
    
    if result['success']:
        logger.success(f"Found {len(result['documents'])} PDF URLs:")
        for doc in result['documents']:
            logger.info(f"  - {doc['document_type']}: {doc['title']}")
            logger.info(f"    URL: {doc['url']}")
            if doc.get('description'):
                logger.info(f"    Description: {doc['description']}")
    else:
        logger.error(f"URL search failed: {result.get('error', 'Unknown error')}")
        logger.info(f"Summary: {result.get('search_summary', 'No summary available')}")
    
    # Example: Find latest news PDF URLs for JPMorgan
    logger.info("Searching for latest PDF news URLs about JPMorgan...")
    news_result = await finder.find_news_pdf_urls("finance.yahoo.com", "JPMorgan")
    
    if news_result['success']:
        logger.success(f"Found {len(news_result['documents'])} news PDF URLs:")
        for doc in news_result['documents']:
            logger.info(f"  - {doc['document_type']}: {doc['title']}")
            logger.info(f"    URL: {doc['url']}")
    else:
        logger.error(f"News URL search failed: {news_result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    asyncio.run(main())
