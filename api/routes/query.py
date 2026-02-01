# Query Route
"""
Single endpoint for ALL user queries.

POST /api/v1/query - Ask anything, LLM decides how to handle it

The LLM automatically determines if you're asking about:
- Your data (queries the user's uploaded tables)
- Domain knowledge (GST rates, rules, etc. if configured)
- Compliance checks
- Table/data structure info
- General questions
"""

import time
from typing import Tuple
from fastapi import APIRouter, Depends

from api.auth import get_current_customer
from api.models import QueryRequest, QueryResponse
from core.customer import CustomerManager
from orchestration.workflow import AgentWorkflow


router = APIRouter(tags=["query"])


def get_workflow(customer_id: str) -> AgentWorkflow:
    """Get workflow instance for customer."""
    manager = CustomerManager()
    ctx = manager.get_customer(customer_id)
    ctx.ensure_exists()
    return AgentWorkflow(customer=ctx)


@router.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    customer: Tuple[str, dict] = Depends(get_current_customer)
):
    """
    Ask anything - the AI figures out what to do.
    
    Examples:
    - "Show me my tables"
    - "What columns are in <table_name>?"
    - "Total of <column> grouped by <another_column>"
    - "Show me data from the last month"
    - "Analyze my data folder"
    
    The LLM automatically:
    1. Understands your intent
    2. Routes to the right handler (data/knowledge/etc)
    3. Returns the response
    """
    customer_id, _ = customer
    start_time = time.time()
    
    try:
        workflow = get_workflow(customer_id)
        
        # LLM handles everything
        answer = workflow.run(request.query)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Check if error response
        is_error = not answer or answer.startswith("❌")
        
        return QueryResponse(
            success=not is_error,
            query=request.query,
            answer=answer or "I couldn't process your request. Please try again.",
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        return QueryResponse(
            success=False,
            query=request.query,
            answer=f"Error: {str(e)}",
            processing_time_ms=processing_time
        )
