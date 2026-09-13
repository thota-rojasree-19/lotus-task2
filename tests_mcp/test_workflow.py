import pytest

@pytest.mark.asyncio
async def test_workflow(mcp_client):
    # 1. listMenu
    menu_result = await mcp_client.call_tool("listMenu", {})
    # Since call_tool returns a list of TextContent objects or similar
    # Let's just verify it didn't throw an error.

    # 2. createCustomer
    customer_args = {
        "name": "MCP Tester",
        "email": "mcp@example.com",
        "phone": "555-0000"
    }
    customer_result = await mcp_client.call_tool("createCustomer", customer_args)
    # 3. getCustomer logic isn't an op, but we can list tables
    tables = await mcp_client.call_tool("listDiningTables", {})

    # 4. createOrder
    order_args = {
        "customer_id": 1,
        "items": [
            {"menu_item_id": 1, "quantity": 2}
        ]
    }
    order_result = await mcp_client.call_tool("createOrder", order_args)

    # 5. updateOrderStatus: NEW -> PREPARING
    update_args_prep = {
        "id": 1,
        "status": "PREPARING"
    }
    await mcp_client.call_tool("updateOrderStatus", update_args_prep)

    # PREPARING -> READY
    update_args_ready = {
        "id": 1,
        "status": "READY"
    }
    await mcp_client.call_tool("updateOrderStatus", update_args_ready)

    # READY -> COMPLETED
    update_args_comp = {
        "id": 1,
        "status": "COMPLETED"
    }
    await mcp_client.call_tool("updateOrderStatus", update_args_comp)

