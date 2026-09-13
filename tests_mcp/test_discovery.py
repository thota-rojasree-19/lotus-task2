import pytest

@pytest.mark.asyncio
async def test_tool_discovery(mcp_client):
    tools = await mcp_client.list_tools()
    
    expected_tools = {
        "listMenu",
        "getMenuItem",
        "createCustomer",
        "listDiningTables",
        "createReservation",
        "getReservation",
        "createOrder",
        "getOrder",
        "updateOrderStatus",
        "listCustomerOrders"
    }
    
    # FastMCP client list_tools() usually returns a list of tool objects or similar.
    # The client might return an object with a .tools list. Let's handle both.
    if hasattr(tools, 'tools'):
        tool_names = {t.name for t in tools.tools}
    else:
        # Assuming it's a list or dictionary
        try:
            tool_names = {t.name for t in tools}
        except AttributeError:
            tool_names = {t["name"] for t in tools}
            
    assert tool_names == expected_tools, f"Expected {expected_tools}, got {tool_names}"
