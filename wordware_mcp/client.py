import httpx
import json
import os
import asyncio
from typing import Dict, Any, Optional, List, Callable

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
        self.client = httpx.AsyncClient(timeout=300.0)  # Increase timeout to 5 minutes for long-running research tasks
        
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
    
    async def _process_sse_stream(self, stream_url: str) -> Dict[str, Any]:
        """Process a Server-Sent Events stream to get all value events.
        
        Args:
            stream_url: The URL of the SSE stream
            
        Returns:
            Dictionary containing all value events from the stream
        """
        # Dictionary to store all received value events
        value_events = {}
        # Dictionary to store accumulated delta events
        delta_paths = {}
        
        max_wait_time = 180  # Maximum wait time in seconds
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with self.client.stream('GET', stream_url) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    # Check if the maximum wait time has been exceeded
                    current_time = asyncio.get_event_loop().time()
                    if current_time - start_time > max_wait_time:
                        print(f"Maximum wait time ({max_wait_time}s) exceeded. Breaking.")
                        break
                    
                    if line.startswith('data:'):
                        data = line[5:].strip()
                        if not data:
                            continue
                            
                        try:
                            event_data = json.loads(data)
                            event_type = event_data.get("type", "unknown")
                            
                            # Process 'value' type events
                            if event_type == "value":
                                path = event_data.get("path", "unknown_path")
                                value = event_data.get("value", {})
                                value_events[path] = value
                            
                            # Process 'delta' type events - as a fallback option
                            elif event_type == "delta":
                                path = event_data.get("path", "")
                                delta = event_data.get("delta", {})
                                
                                # Initialize the path if it doesn't exist yet
                                if path not in delta_paths:
                                    delta_paths[path] = ""
                                
                                # Update the text for this path for 'text' type
                                if delta.get("type") == "text" and isinstance(delta_paths[path], str):
                                    delta_paths[path] += delta.get("value", "")
                            
                            # End processing when a completion event is received
                            elif event_type == "status" and event_data.get("status") == "completed":
                                print("Stream completed.")
                                break
                            
                            # Completion events with output data
                            elif event_type == "ai.wordware.run.completed.v1":
                                print("Completion event received.")
                                if "data" in event_data and "output" in event_data["data"]:
                                    # Add completion event output data if available
                                    value_events["completion_output"] = event_data["data"]["output"]
                                break
                                
                        except json.JSONDecodeError:
                            print(f"Failed to parse event data: {data}")
        
        except httpx.HTTPStatusError as e:
            print(f"Error processing SSE stream: {e}")
            return {"error": f"Stream error: {e}"}
        
        # If there are no value events but there are accumulated deltas, use them as a fallback
        if not value_events and delta_paths:
            # Convert accumulated deltas to output format
            for path, content in delta_paths.items():
                value_events[path] = content
        
        # Return all collected value events
        return {"output": value_events}
    
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
        
        # Prepare the payload using the new API format
        payload = {
            "data": {
                "type": "runs",
                "attributes": {
                    "version": "1.0",
                    "inputs": {
                        "Full Name": full_name,
                        "Company": company,
                        "URL": url
                    },
                    "webhooks": []
                }
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "*/*"
        }
        
        try:
            # Make the API call to initiate the run
            response = await self.client.post(
                f"{self.api_url}/v1/apps/{flow_id}/runs",
                headers=headers,
                json=payload
            )
            
            response.raise_for_status()
            run_data = response.json()
            
            # Extract the stream URL
            stream_url = run_data.get("data", {}).get("links", {}).get("stream")
            
            if not stream_url:
                return {"error": "No stream URL in response", "response": run_data}
            
            # Process the stream to get all value events
            print(f"Processing stream for founder research: {full_name}")
            result = await self._process_sse_stream(stream_url)
            return result
            
        except httpx.HTTPStatusError as e:
            print(f"Error calling Wordware API: {e.response.status_code} {e.response.text}")
            return {"error": f"API error: {e.response.status_code}", "message": e.response.text}
        except json.JSONDecodeError as e:
            return {"error": f"Failed to parse Wordware API response: {e}"}
        except Exception as e:
            return {"error": f"Unexpected error: {e}"}
    
    async def research_topic(self, query: str) -> Dict[str, Any]:
        """Research a topic using Wordware's general research capabilities.
        
        Args:
            query: The topic or question to research
            
        Returns:
            Research results from Wordware
        """
        # In the future, when a specific ID for topic research is available,
        # we can implement a real API call. For now, we return mock data.
        return {
            "output": {
                "research": f"Research on topic: {query}\n\n"
                           f"This is a mock response. In a real implementation, "
                           f"this would call the Wordware API with the appropriate flow ID "
                           f"for general topic research."
            }
        }
    
    async def save_to_notion(self, title: str, body: str) -> Dict[str, Any]:
        """Save content to Notion using Wordware's integration.
        
        Args:
            title: The title of the Notion page
            body: The content body of the Notion page
            
        Returns:
            Result of the operation
        """
        # Get Notion integration flow ID from config or use default
        flow_id = self.config.get("notion_integration_flow_id", "55921f92-9374-444b-879a-3a7820a29850")
        
        # Prepare the payload using the required API format
        payload = {
            "data": {
                "type": "runs",
                "attributes": {
                    "version": "1.0",
                    "inputs": {
                        "title": title,
                        "body": body
                    },
                    "webhooks": []
                }
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "*/*"
        }
        
        try:
            # Make the API call to initiate the run
            response = await self.client.post(
                f"{self.api_url}/v1/apps/{flow_id}/runs",
                headers=headers,
                json=payload
            )
            
            response.raise_for_status()
            run_data = response.json()
            
            # Extract the stream URL
            stream_url = run_data.get("data", {}).get("links", {}).get("stream")
            
            if not stream_url:
                return {"error": "No stream URL in response", "response": run_data}
            
            # Process the stream to get all value events
            print(f"Processing stream for Notion save: {title}")
            result = await self._process_sse_stream(stream_url)
            return result
            
        except httpx.HTTPStatusError as e:
            print(f"Error calling Wordware API: {e.response.status_code} {e.response.text}")
            return {"error": f"API error: {e.response.status_code}", "message": e.response.text}
        except json.JSONDecodeError as e:
            return {"error": f"Failed to parse Wordware API response: {e}"}
        except Exception as e:
            return {"error": f"Unexpected error: {e}"}
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose() 