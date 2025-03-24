"""
Research Agent for MCP integration with Wordware.
"""

from typing import Dict, Any, List
import json
from wordware_mcp.client import WordwareClient

class ResearchAgent:
    """Research Agent for finding information using Wordware API."""
    
    def __init__(self):
        """Initialize the Research Agent."""
        self.client = WordwareClient()
    
    async def research_person(self, full_name: str, company: str = "", url: str = "") -> Dict[str, Any]:
        """
        Research information about a person, such as a founder or executive.
        
        Args:
            full_name: The full name of the person to research
            company: The company the person is associated with (optional)
            url: A relevant URL for additional context (optional)
            
        Returns:
            Detailed information about the person
        """
        return await self.client.research_person(full_name, company, url)
    
    async def research_topic(self, query: str) -> List[Dict[str, Any]]:
        """
        Research a general topic using Wordware's research capabilities.
        
        Args:
            query: The topic or question to research
            
        Returns:
            Research results as a list of findings
        """
        return await self.client.research_topic(query)
    
    async def format_person_research(self, result: Dict[str, Any]) -> str:
        """
        Format person research results into readable text.
        
        Args:
            result: Research results from the Wordware API
            
        Returns:
            Formatted research results as text
        """
        if "error" in result:
            return f"Error performing research: {result.get('error', 'Unknown error')}"
        
        # In a real implementation, you would parse the specific structure
        # of the Wordware API response. This is a simplified example.
        
        # If we have actual output from the API, format it
        if "output" in result:
            output = result["output"]
            # Format depends on actual API response structure
            if isinstance(output, dict):
                # Try to extract common fields that might be in the response
                bio = output.get("biography", "No biography available")
                experience = output.get("experience", [])
                education = output.get("education", [])
                
                formatted = f"# Research Results\n\n"
                formatted += f"## Biography\n{bio}\n\n"
                
                if experience:
                    formatted += "## Professional Experience\n"
                    for exp in experience:
                        if isinstance(exp, dict):
                            role = exp.get("role", "Unknown role")
                            company = exp.get("company", "Unknown company")
                            period = exp.get("period", "")
                            formatted += f"- {role} at {company} {period}\n"
                        else:
                            formatted += f"- {exp}\n"
                    formatted += "\n"
                
                if education:
                    formatted += "## Education\n"
                    for edu in education:
                        if isinstance(edu, dict):
                            degree = edu.get("degree", "")
                            institution = edu.get("institution", "")
                            year = edu.get("year", "")
                            formatted += f"- {degree} from {institution} {year}\n"
                        else:
                            formatted += f"- {edu}\n"
                    formatted += "\n"
                
                return formatted
            
            # If output is a string, return it directly
            elif isinstance(output, str):
                return output
        
        # Fallback to returning the raw JSON
        return f"Research results:\n\n{json.dumps(result, indent=2)}"
    
    async def format_topic_research(self, results: List[Dict[str, Any]]) -> str:
        """
        Format topic research results into readable text.
        
        Args:
            results: Research results from the Wordware API
            
        Returns:
            Formatted research results as text
        """
        if not results:
            return "No research results found."
        
        formatted = "# Research Findings\n\n"
        
        for i, result in enumerate(results, 1):
            title = result.get("title", "Untitled")
            snippet = result.get("snippet", "No details available")
            url = result.get("url", "")
            
            formatted += f"## {i}. {title}\n"
            formatted += f"{snippet}\n"
            if url:
                formatted += f"Source: {url}\n"
            formatted += "\n"
        
        return formatted
    
    async def close(self):
        """Clean up resources."""
        await self.client.close() 