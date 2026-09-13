import pytest
from fastmcp.exceptions import FastMCPError

@pytest.mark.asyncio
async def test_failures(mcp_client):
    # duplicate customer email
    customer_args = {
        "name": "Fail Tester",
        "email": "fail@example.com",
        "phone": "555-0001"
    }
    await mcp_client.call_tool("createCustomer", customer_args)
    
    # Should throw exception or return an error string
    try:
        res = await mcp_client.call_tool("createCustomer", customer_args)
        # FastMCP might just return an error text instead of raising
        assert "Error" in str(res) or "409" in str(res)
    except Exception as e:
        assert "409" in str(e) or "Conflict" in str(e)

    # invalid order status transition
    update_args = {
        "id": 9999, # unknown id
        "status": "COMPLETED"
    }
    try:
        res = await mcp_client.call_tool("updateOrderStatus", update_args)
        assert "Error" in str(res) or "404" in str(res)
    except Exception as e:
        assert "404" in str(e)

