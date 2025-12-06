from fastmcp import FastMCP
import random

mcp = FastMCP("Random Number Generator")

# MODERN API STYLE — individual parameters with type hints
@mcp.tool()
def generate_random_number(min_value: float, max_value: float) -> dict:
    """
    Generate a random number between min_value and max_value.
    
    Args:
        min_value: The minimum value (inclusive)
        max_value: The maximum value (inclusive)
    
    Returns:
        A dictionary with the random number or an error message
    """
    if min_value > max_value:
        return {"error": "min_value must be <= max_value"}

    return {
        "random_number": random.uniform(min_value, max_value)
    }


# MODERN API resource — returns string content directly
@mcp.resource("random://info")
def random_number_info() -> str:
    """Information about the Random Number Generator service"""
    return """Random Number Generator v1.0.0
    
Description: Generates a random number between a specified minimum and maximum value.
Usage: Call generate_random_number with min_value and max_value parameters."""


if __name__ == "__main__":
    mcp.run()