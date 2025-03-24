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
    
    async def research_topic(self, query: str) -> Dict[str, Any]:
        """
        Research a general topic using Wordware's research capabilities.
        
        Args:
            query: The topic or question to research
            
        Returns:
            Research results as a structured dictionary
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
        
        # Check for output data
        if "output" not in result:
            return f"No research output available. Raw response: {json.dumps(result, indent=2)}"
        
        output = result["output"]
        
        # Format the response as Markdown
        formatted = "# Research Results\n\n"
        
        # Prepare a dictionary of specific sections that need special formatting
        special_sections = {
            "questions": "## Interview Questions",
            "Web search with Exa.researchRCompany": "## Company Overview",
            "Web search with Exa.researchRCompany.finalresearchCompany": "## Company Research",
            "Website similarity search.competitionfull.competitionfullSonar.finalcompetitonanalysis": "## Competition Analysis",
            "completion_output": "## Analysis"
        }
        
        # First process special sections in a specific order, if they exist
        special_keys = list(set(special_sections.keys()) & set(output.keys()))
        special_keys.sort(key=lambda k: list(special_sections.keys()).index(k) if k in special_sections else 999)
        
        for key in special_keys:
            section_title = special_sections.get(key, f"## {key.replace('_', ' ').title()}")
            content = output[key]
            
            formatted += f"{section_title}\n\n"
            if isinstance(content, str):
                formatted += f"{content}\n\n"
            elif isinstance(content, dict) and "generation" in content:
                # Special handling for "generation" format
                formatted += f"{content['generation']}\n\n"
            else:
                # Output JSON for structured data
                formatted += f"```json\n{json.dumps(content, indent=2)}\n```\n\n"
        
        # Then process all other keys
        other_keys = list(set(output.keys()) - set(special_keys))
        
        if other_keys:
            formatted += "## Additional Information\n\n"
            
            for key in other_keys:
                content = output[key]
                formatted += f"### {key.replace('_', ' ').title()}\n\n"
                
                if isinstance(content, str):
                    formatted += f"{content}\n\n"
                else:
                    formatted += f"```json\n{json.dumps(content, indent=2)}\n```\n\n"
        
        return formatted
    
    async def format_topic_research(self, results: Dict[str, Any]) -> str:
        """
        Format topic research results into readable text.
        
        Args:
            results: Research results from the Wordware API
            
        Returns:
            Formatted research results as text
        """
        if "error" in results:
            return f"Error performing research: {results.get('error', 'Unknown error')}"
            
        if "output" not in results:
            return f"No research output available. Raw response: {json.dumps(results, indent=2)}"
            
        output = results["output"]
        
        # If output is a string
        if isinstance(output, str):
            return output
            
        # If output is a dictionary
        if isinstance(output, dict):
            # If there's a research field
            if "research" in output:
                return f"# Research on Topic\n\n{output['research']}"
                
            # Other cases
            formatted = "# Research Findings\n\n"
            
            for key, value in output.items():
                formatted += f"## {key.replace('_', ' ').title()}\n"
                if isinstance(value, str):
                    formatted += f"{value}\n\n"
                else:
                    formatted += f"```json\n{json.dumps(value, indent=2)}\n```\n\n"
            
            return formatted
            
        # If nothing matched, return raw JSON
        return f"Research results:\n\n{json.dumps(results, indent=2)}"
    
    async def save_to_notion(self, title: str, body: str) -> Dict[str, Any]:
        """
        Save content to Notion using Wordware's integration.
        
        Args:
            title: The title of the Notion page
            body: The content body of the Notion page
            
        Returns:
            Result of the operation
        """
        return await self.client.save_to_notion(title, body)
    
    async def format_notion_result(self, result: Dict[str, Any]) -> str:
        """
        Format the result of a Notion save operation.
        
        Args:
            result: Result from the Wordware API
            
        Returns:
            Formatted result as text
        """
        if "error" in result:
            return f"❌ Error saving to Notion: {result.get('error', 'Unknown error')}"
        
        # Check for output data
        if "output" not in result:
            return f"❌ No operation result data available. Raw response: {json.dumps(result, indent=2)}"
        
        output = result["output"]
        
        # Check for successful save information
        if "completion_output" in output and isinstance(output["completion_output"], dict):
            if "url" in output["completion_output"]:
                url = output["completion_output"]["url"]
                return f"✅ Successfully saved to Notion!\n📄 Link to the created page: {url}"
            else:
                return f"✅ Successfully saved to Notion!\n📄 Details: {json.dumps(output['completion_output'], indent=2)}"
        
        # If there's any useful information in the response, try to extract it
        for key, value in output.items():
            if isinstance(value, dict) and "url" in value:
                return f"✅ Successfully saved to Notion!\n📄 Link to the created page: {value['url']}"
        
        # If nothing was found, just return the raw response
        return f"✅ Operation completed. Result:\n```json\n{json.dumps(output, indent=2)}\n```"
    
    async def close(self):
        """Clean up resources."""
        await self.client.close() 