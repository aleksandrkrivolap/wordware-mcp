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
        
        # Проверяем наличие выходных данных
        if "output" not in result:
            return f"No research output available. Raw response: {json.dumps(result, indent=2)}"
        
        output = result["output"]
        
        # Форматируем ответ в виде Markdown
        formatted = "# Research Results\n\n"
        
        # Подготовим словарь конкретных секций, которые нам нужно форматировать особым образом
        special_sections = {
            "questions": "## Interview Questions",
            "Web search with Exa.researchRCompany": "## Company Overview",
            "Web search with Exa.researchRCompany.finalresearchCompany": "## Company Research",
            "Website similarity search.competitionfull.competitionfullSonar.finalcompetitonanalysis": "## Competition Analysis",
            "completion_output": "## Analysis"
        }
        
        # Сначала обработаем специальные секции в определенном порядке, если они есть
        special_keys = list(set(special_sections.keys()) & set(output.keys()))
        special_keys.sort(key=lambda k: list(special_sections.keys()).index(k) if k in special_sections else 999)
        
        for key in special_keys:
            section_title = special_sections.get(key, f"## {key.replace('_', ' ').title()}")
            content = output[key]
            
            formatted += f"{section_title}\n\n"
            if isinstance(content, str):
                formatted += f"{content}\n\n"
            elif isinstance(content, dict) and "generation" in content:
                # Специальная обработка для формата с "generation"
                formatted += f"{content['generation']}\n\n"
            else:
                # Выводим JSON для структурированных данных
                formatted += f"```json\n{json.dumps(content, indent=2)}\n```\n\n"
        
        # Затем обработаем все остальные ключи
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
        
        # Если output это строка
        if isinstance(output, str):
            return output
            
        # Если output это словарь
        if isinstance(output, dict):
            # Если есть поле research
            if "research" in output:
                return f"# Research on Topic\n\n{output['research']}"
                
            # Другие случаи
            formatted = "# Research Findings\n\n"
            
            for key, value in output.items():
                formatted += f"## {key.replace('_', ' ').title()}\n"
                if isinstance(value, str):
                    formatted += f"{value}\n\n"
                else:
                    formatted += f"```json\n{json.dumps(value, indent=2)}\n```\n\n"
            
            return formatted
            
        # Если ничего не подошло, возвращаем сырой JSON
        return f"Research results:\n\n{json.dumps(results, indent=2)}"
    
    async def close(self):
        """Clean up resources."""
        await self.client.close() 