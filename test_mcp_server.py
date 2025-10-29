#!/usr/bin/env python3
"""
Test script to verify the MCP database server is working properly.
Tests connection, available tools, and basic operations.
"""

import asyncio
import sys
import subprocess
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions


async def test_mcp_connection():
    """Test basic MCP server connection and tool discovery."""
    print("=" * 60)
    print("Testing MCP Server Connection")
    print("=" * 60)
    
    try:
        # Create client with MCP server configuration
        options = ClaudeAgentOptions(
            model="haiku",
            mcp_servers={
                "database": {
                    "command": "-m",
                    "args": ["database.db_mcp"],
                }
            },
        )
        
        client = ClaudeSDKClient(options=options)
        print("✓ ClaudeSDKClient created successfully")
        
        # Connect to the server
        await client.connect()
        print("✓ Connected to MCP server")
        
        return client
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return None


async def test_tool_availability(client):
    """Test that tools are available from the MCP server."""
    print("\n" + "=" * 60)
    print("Testing Tool Availability")
    print("=" * 60)
    
    try:
        # Send a query that asks Claude to use the database tools
        test_query = "What tools are available in the database MCP server?"
        
        await client.query(test_query)
        
        response_text = ""
        async for message in client.receive_response():
            response_text += str(message)
        
        print("✓ Tool discovery query successful")
        print(f"Response preview: {response_text[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ Tool discovery failed: {e}")
        return False


async def test_get_unique_topics(client):
    """Test the get_unique_topics tool."""
    print("\n" + "=" * 60)
    print("Testing get_unique_topics Tool")
    print("=" * 60)
    
    try:
        query = "Please use the get_unique_topics tool to retrieve all available topics in the question bank."
        
        await client.query(query)
        
        response_text = ""
        async for message in client.receive_response():
            response_text += str(message)
        
        if response_text and "topic" in response_text.lower():
            print("✓ get_unique_topics tool executed successfully")
            print(f"Response: {response_text[:300]}...")
            return True
        else:
            print("⚠ Tool executed but unclear if data was returned")
            print(f"Response: {response_text}")
            return False
            
    except Exception as e:
        print(f"✗ get_unique_topics tool failed: {e}")
        return False


async def test_get_skill_level_pairs(client):
    """Test the get_skill_level_pairs tool."""
    print("\n" + "=" * 60)
    print("Testing get_skill_level_pairs Tool")
    print("=" * 60)
    
    try:
        query = "Please use the get_skill_level_pairs tool to retrieve skill level information."
        
        await client.query(query)
        
        response_text = ""
        async for message in client.receive_response():
            response_text += str(message)
        
        if response_text:
            print("✓ get_skill_level_pairs tool executed successfully")
            print(f"Response: {response_text[:300]}...")
            return True
        else:
            print("⚠ Tool executed but no response received")
            return False
            
    except Exception as e:
        print(f"✗ get_skill_level_pairs tool failed: {e}")
        return False


async def test_add_memory_entry(client):
    """Test the add_memory_entry tool."""
    print("\n" + "=" * 60)
    print("Testing add_memory_entry Tool")
    print("=" * 60)
    
    try:
        query = 'Please use the add_memory_entry tool to add this test memory: "Test entry from MCP server verification script"'
        
        await client.query(query)
        
        response_text = ""
        async for message in client.receive_response():
            response_text += str(message)
        
        if response_text and ("memory" in response_text.lower() or "added" in response_text.lower()):
            print("✓ add_memory_entry tool executed successfully")
            print(f"Response: {response_text[:300]}...")
            return True
        else:
            print("⚠ Tool executed but unclear if memory was added")
            print(f"Response: {response_text}")
            return False
            
    except Exception as e:
        print(f"✗ add_memory_entry tool failed: {e}")
        return False


async def test_update_skill_level(client):
    """Test the update_skill_level tool."""
    print("\n" + "=" * 60)
    print("Testing update_skill_level Tool")
    print("=" * 60)
    
    try:
        query = "Please use the update_skill_level tool to set the skill level for 'Algebra' to 3."
        
        await client.query(query)
        
        response_text = ""
        async for message in client.receive_response():
            response_text += str(message)
        
        if response_text and ("skill" in response_text.lower() or "updated" in response_text.lower()):
            print("✓ update_skill_level tool executed successfully")
            print(f"Response: {response_text[:300]}...")
            return True
        else:
            print("⚠ Tool executed but unclear if level was updated")
            print(f"Response: {response_text}")
            return False
            
    except Exception as e:
        print(f"✗ update_skill_level tool failed: {e}")
        return False


async def main():
    """Run all MCP server tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " MCP DATABASE SERVER VERIFICATION SCRIPT ".center(58) + "║")
    print("╚" + "=" * 58 + "╝")
    
    # Connect to server
    client = await test_mcp_connection()
    
    if not client:
        print("\n✗ Failed to connect to MCP server. Exiting.")
        return False
    
    all_passed = True
    
    try:
        # Run all tests
        if not await test_tool_availability(client):
            all_passed = False
        
        if not await test_get_unique_topics(client):
            all_passed = False
        
        if not await test_get_skill_level_pairs(client):
            all_passed = False
        
        if not await test_add_memory_entry(client):
            all_passed = False
        
        if not await test_update_skill_level(client):
            all_passed = False
        
    finally:
        # Disconnect
        await client.disconnect()
        print("\n✓ Disconnected from MCP server")
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    if all_passed:
        print("✓ All tests passed!")
        print("\nThe MCP server is working properly and all tools are accessible.")
    else:
        print("⚠ Some tests failed or had warnings.")
        print("\nPlease review the output above for details.")
    
    return all_passed


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        sys.exit(1)
