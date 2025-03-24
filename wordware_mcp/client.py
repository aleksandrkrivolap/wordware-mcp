import httpx
import json
import os
from typing import Dict, Any, Optional, List

class WordwareClient:
    """Client for making requests to Wordware API."""
    
    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None):
        """Initialize the Wordware client.
        
        Args:
            api_key: API key for the Wordware service. If not provided,
                    will try to load from environment variables.
            api_url: Base URL for the Wordware API. If not provided,
                    will try to load from environment variables.
        """
        self.api_key = api_key or os.environ.get("WORDWARE_API_KEY", "")
        self.api_url = api_url or os.environ.get("WORDWARE_API_URL", "https://api.wordware.ai")
        self.client = httpx.AsyncClient(timeout=120.0)  # Longer timeout for research tasks
        
        # Load configuration
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from config.json."""
        config_path = os.environ.get("CONFIG_PATH", "./config.json")
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading config: {e}")
            return {}
    
    async def research_person(self, full_name: str, company: str = "", url: str = "") -> Dict[str, Any]:
        """Research a person using Wordware's specialized research agent.
        
        Args:
            full_name: The full name of the person to research
            company: The company the person is associated with (optional)
            url: A relevant URL for additional context (optional)
            
        Returns:
            Research results from Wordware
        """
        # Get founder research flow ID from config
        flow_id = self.config.get("founder_research_flow_id", "2ef1755d-febd-47d6-b96d-b35e719da0f9")
        
        # Prepare the payload
        payload = {
            "inputs": {
                "Full Name": full_name,
                "Company": company,
                "URL": url
            },
            "version": "^1.0"
        }
        
        # Make the API call
        response = await self.client.post(
            f"{self.api_url}/api/released-app/{flow_id}/run",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=payload
        )
        
        try:
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError:
            # Log the error (in a real app, we'd use proper logging)
            print(f"Error calling Wordware API: {response.status_code} {response.text}")
            return {"error": f"API error: {response.status_code}", "message": response.text}
        except json.JSONDecodeError:
            return {"error": "Failed to parse Wordware API response: " + response.text}
    
    async def research_topic(self, query: str) -> List[Dict[str, Any]]:
        """Research a topic using Wordware's general research capabilities.
        
        Args:
            query: The topic or question to research
            
        Returns:
            A list of research results
        """
        # For now, we'll return mocked data since we don't have the specific flow ID
        # for general research. In a real implementation, you would use the appropriate
        # flow ID and API endpoint.
        
        # Fallback to mock data for demonstration
        return [
            {
                "title": f"Wordware research result for: {query}",
                "snippet": "This would be actual research results from Wordware API. In a production environment, this would use the appropriate Wordware flow for general topic research.",
                "url": "https://wordware.ai/research-results"
            },
            {
                "title": f"Additional insights on: {query}",
                "snippet": "Wordware Research Agents provide comprehensive insights by analyzing multiple sources and synthesizing the information.",
                "url": "https://wordware.ai/methodology"
            }
        ]
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose() 