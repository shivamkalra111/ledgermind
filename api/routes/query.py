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

Security:
- Input sanitization for prompt injection protection
- Blocked requests return 400 with security message
"""

import time
import logging
from typing import Tuple
from fastapi import APIRouter, Depends, HTTPException

from api.auth import get_current_customer
from api.models import QueryRequest, QueryResponse
from core.customer import CustomerManager
from core.security import sanitize_user_input, ThreatLevel
from orchestration.workflow import AgentWorkflow

logger = logging.getLogger(__name__)


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
    
    Security:
    - Input is validated for prompt injection attacks
    - Malicious queries are blocked with 400 status
    """
    customer_id, _ = customer
    start_time = time.time()
    
    # Security: Validate input at API boundary
    security_result = sanitize_user_input(request.query)
    
    if security_result.blocked:
        logger.warning(
            f"Blocked query from customer {customer_id}. "
            f"Threat: {security_result.threat_level.value}. "
            f"Issues: {security_result.threats_detected}"
        )
        raise HTTPException(
            status_code=400,
            detail="Your request could not be processed. Please rephrase your question."
        )
    
    # Log if threats were detected but not blocked
    if security_result.threats_detected:
        logger.info(
            f"Sanitized query from customer {customer_id}. "
            f"Threats: {security_result.threats_detected}"
        )
    
    try:
        workflow = get_workflow(customer_id)
        
        # Use sanitized input for processing
        sanitized_query = security_result.sanitized_input
        answer = workflow.run(sanitized_query)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Check if error response
        is_error = not answer or answer.startswith("❌")
        
        return QueryResponse(
            success=not is_error,
            query=request.query,  # Return original query in response
            answer=answer or "I couldn't process your request. Please try again.",
            processing_time_ms=processing_time
        )
        
    except ValueError as e:
        # Security-related errors from LLM client
        processing_time = int((time.time() - start_time) * 1000)
        return QueryResponse(
            success=False,
            query=request.query,
            answer=str(e),
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"Query error for customer {customer_id}: {str(e)}")
        return QueryResponse(
            success=False,
            query=request.query,
            answer=f"Error: {str(e)}",
            processing_time_ms=processing_time
        )
