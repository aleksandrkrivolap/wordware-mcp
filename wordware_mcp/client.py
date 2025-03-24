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
        self.client = httpx.AsyncClient(timeout=300.0)  # Увеличиваем таймаут до 5 минут для длительных исследований
        
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
        # Словарь для хранения всех полученных value-событий
        value_events = {}
        # Словарь для хранения накопленных дельта-событий
        delta_paths = {}
        
        max_wait_time = 180  # Максимальное время ожидания в секундах
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with self.client.stream('GET', stream_url) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    # Проверяем, не превышен ли таймаут
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
                            
                            # Обработка событий типа 'value'
                            if event_type == "value":
                                path = event_data.get("path", "unknown_path")
                                value = event_data.get("value", {})
                                value_events[path] = value
                            
                            # Обработка событий типа 'delta' - на всякий случай, для резервного варианта
                            elif event_type == "delta":
                                path = event_data.get("path", "")
                                delta = event_data.get("delta", {})
                                
                                # Инициализируем путь, если его еще нет
                                if path not in delta_paths:
                                    delta_paths[path] = ""
                                
                                # Обновляем текст по пути для типа text
                                if delta.get("type") == "text" and isinstance(delta_paths[path], str):
                                    delta_paths[path] += delta.get("value", "")
                            
                            # Завершаем обработку при получении события завершения
                            elif event_type == "status" and event_data.get("status") == "completed":
                                print("Stream completed.")
                                break
                            
                            # События завершения с выходными данными
                            elif event_type == "ai.wordware.run.completed.v1":
                                print("Completion event received.")
                                if "data" in event_data and "output" in event_data["data"]:
                                    # Добавляем выходные данные события завершения, если они есть
                                    value_events["completion_output"] = event_data["data"]["output"]
                                break
                                
                        except json.JSONDecodeError:
                            print(f"Failed to parse event data: {data}")
        
        except httpx.HTTPStatusError as e:
            print(f"Error processing SSE stream: {e}")
            return {"error": f"Stream error: {e}"}
        
        # Если нет событий value, но есть накопленные дельты, используем их как резерв
        if not value_events and delta_paths:
            # Преобразуем накопленные дельты в формат для вывода
            for path, content in delta_paths.items():
                value_events[path] = content
        
        # Возвращаем все собранные события типа value
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
        # В будущем, когда будет доступен специфический ID для исследования тем,
        # можно реализовать реальный вызов API. Пока возвращаем моковые данные.
        return {
            "output": {
                "research": f"Research on topic: {query}\n\n"
                           f"This is a mock response. In a real implementation, "
                           f"this would call the Wordware API with the appropriate flow ID "
                           f"for general topic research."
            }
        }
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose() 