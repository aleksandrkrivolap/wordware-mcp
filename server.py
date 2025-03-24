from mcp.server.fastmcp import FastMCP

# Create a FastMCP instance with your namespace
mcp = FastMCP("simple-tools")

@mcp.tool()
async def echo(message: str) -> str:
    """
    Echo the input message.
    
    Args:
        message: The message to echo
    
    Returns:
        The same message
    """
    return f"Echo: {message}"

@mcp.tool()
async def add(a: int, b: int) -> int:
    """
    Add two numbers.
    
    Args:
        a: First number
        b: Second number
    
    Returns:
        The sum of a and b
    """
    return a + b

@mcp.tool()
async def greet(name: str = "World") -> str:
    """
    Greet a person.
    
    Args:
        name: The name of the person to greet
    
    Returns:
        A greeting message
    """
    return f"Hello, {name}!"

if __name__ == "__main__":
    # Run the server
    mcp.run(transport="stdio") 