# Document Link Extractor MCP Server

An intelligent MCP (Model Context Protocol) server that uses browser-use to extract document download links from websites. Features both basic link extraction and AI-powered intelligent document finding capabilities.

## Overview

This server provides two levels of functionality:

1. **Basic Link Extraction**: Extract document download links from any website
2. **Intelligent Document Finding**: Use AI agents to navigate and find specific documents like 10-K filings, SEC documents, etc.

## Features

### Basic Features
- **General Purpose**: Works with any website, not just specific domains
- **Document Detection**: Automatically identifies downloadable files (PDF, Excel, Word, etc.)
- **Browser Automation**: Uses browser-use for reliable web scraping
- **Structured Output**: Returns JSON with metadata about each link
- **MCP Compatible**: Works with Claude Desktop and other MCP clients
- **No Downloads**: Only extracts links, never downloads actual files

### Intelligent Features
- **AI-Powered Navigation**: Uses LLM agents to intelligently navigate websites
- **10-K Filing Finder**: Automatically find latest 10-K filings for any company
- **SEC EDGAR Search**: Search SEC database for specific company filings
- **Investor Relations Documents**: Find documents from company investor relations pages
- **Natural Language Tasks**: Can handle complex navigation tasks like "find the latest annual report"

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or install individually
pip install fastmcp browser-use pydantic openai python-dotenv
```

### 🔑 Important: OpenAI API Key Setup

The intelligent features require an OpenAI API key. See [SETUP.md](SETUP.md) for detailed instructions on how to configure your API key.

Quick setup:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

### As a standalone MCP server:

```bash
python server.py
```

### With Claude Desktop:

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "document-link-extractor": {
      "command": "python",
      "args": ["/path/to/browser-use-link-extractor/server.py"]
    }
  }
}
```

## Available Tools

### Basic Tools

#### `get_document_download_links`
Navigate to any website and extract document download links.

**Parameters:**
- `url` (string, required): The URL to navigate to (e.g., 'https://example.com')

**Returns:** JSON structure with document links and metadata

#### `extract_modelcontextprotocol_links`
Convenience tool that automatically navigates to modelcontextprotocol.io and extracts document links.

#### `close_browser`
Clean up the browser session.

### Intelligent Tools

#### `find_documents_intelligent`
Intelligently find any type of documents from a website using AI-powered navigation.

**Parameters:**
- `website_url` (string, required): The website URL to search (e.g., 'finance.yahoo.com')
- `search_query` (string, required): What to search for (e.g., 'JPMorgan latest news PDF', 'annual reports')

**Returns:** Found documents with titles, URLs, types, and search summary

#### `find_pdf_documents`
Find PDF documents on a specific topic from a website using intelligent navigation.

**Parameters:**
- `website_url` (string, required): The website URL to search (e.g., 'finance.yahoo.com')
- `topic` (string, required): Topic to search for (e.g., 'JPMorgan', 'artificial intelligence')

**Returns:** Found PDF documents with titles, URLs, and descriptions

#### `find_latest_news_pdf`
Find the latest news in PDF format for a specific company using intelligent navigation.

**Parameters:**
- `website_url` (string, required): The website URL to search (e.g., 'finance.yahoo.com')
- `company_name` (string, required): Company name to search for (e.g., 'JPMorgan', 'Apple')

**Returns:** Found news articles with PDF URLs, dates, and descriptions

#### `find_annual_reports`
Find annual reports from a company website using intelligent navigation.

**Parameters:**
- `company_url` (string, required): The company website URL (e.g., 'microsoft.com')

**Returns:** Found annual reports with titles, URLs, years, and descriptions

## Example Usage

### Basic Usage
```python
# Navigate to example.com and extract document links
result = await get_document_download_links("https://example.com")
data = json.loads(result)
print(f"Found {data['total_links_found']} document links")
for link in data['document_links']:
    print(f"- {link['text']}: {link['url']} ({link['file_type']})")
```

### Intelligent Usage
```python
# Find any documents about JPMorgan from Yahoo Finance
result = await find_documents_intelligent("finance.yahoo.com", "JPMorgan latest news PDF")
data = json.loads(result)
if data['success']:
    for doc in data['documents']:
        print(f"Found {doc['document_type']}: {doc['title']} at {doc['url']}")

# Find PDF documents about artificial intelligence
result = await find_pdf_documents("finance.yahoo.com", "artificial intelligence")
data = json.loads(result)
if data['success']:
    for doc in data['documents']:
        print(f"Found PDF: {doc['title']} at {doc['url']}")

# Find latest news in PDF format for JPMorgan
result = await find_latest_news_pdf("finance.yahoo.com", "JPMorgan")
data = json.loads(result)
if data['success']:
    for doc in data['documents']:
        print(f"Found news PDF: {doc['title']} at {doc['url']}")

# Find annual reports from Microsoft
result = await find_annual_reports("microsoft.com")
data = json.loads(result)
if data['success']:
    for doc in data['documents']:
        print(f"Found report: {doc['title']} at {doc['url']}")
```

## Example Output

### Basic Link Extraction
```json
{
  "url": "https://example.com",
  "total_links_found": 5,
  "document_links": [
    {
      "text": "Annual Report 2024",
      "url": "https://example.com/reports/annual-2024.pdf",
      "file_type": "PDF",
      "category": "report",
      "is_download": true,
      "source": "example.com"
    }
  ],
  "message": "Found 5 document download links"
}
```

### Intelligent 10-K Finding
```json
{
  "success": true,
  "documents": [
    {
      "title": "Form 10-K Annual Report 2024",
      "url": "https://d18rn0p25nwr6d.cloudfront.net/CIK-0000886982/10-K/2024.pdf",
      "document_type": "10-K",
      "filing_date": "2024-11-01",
      "company_name": "GOLDMAN SACHS GROUP INC"
    }
  ],
  "search_summary": "Successfully navigated to Goldman Sachs investor relations, located SEC filings section, and found the latest 10-K filing",
  "company": "goldmansachs.com",
  "document_type": "10-K"
}
```

## System Prompt

When using this tool, the system should be instructed to:

> "Use intelligent navigation tools to find specific documents. For general document searches, use find_documents_intelligent with natural language queries. For PDF-specific searches, use find_pdf_documents. For news articles in PDF format, use find_latest_news_pdf. For annual reports, use find_annual_reports."

## Supported File Types

The server automatically detects these file types:
- PDF documents
- Excel spreadsheets (.xlsx, .csv)
- Word documents (.doc, .docx)
- PowerPoint presentations (.ppt, .pptx)
- Zip archives
- Text files
- SEC filings (10-K, 10-Q, 8-K, etc.)

## Architecture

This server uses:
- **FastMCP**: Simplified MCP server framework
- **browser-use**: Browser automation with AI agent capabilities
- **Pydantic**: Data validation and serialization
- **OpenAI**: LLM for intelligent navigation
- **Streaming HTTP**: Via stdio transport for MCP compliance

The server maintains persistent browser sessions and can handle both simple link extraction and complex navigation tasks.

## Testing

Run the test scripts to verify functionality:

```bash
# Test basic functionality
python test_server.py

# Test intelligent features
python test_intelligent.py
```

## License

MIT License - See the main browser-use repository for details.
