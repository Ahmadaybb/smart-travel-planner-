from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.auth.dependencies import get_current_user
from app.models.database import User, AgentRun, ToolCallLog
from app.agent.agent import run_agent
from app.services.webhook import deliver_webhook
import json
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/agent", tags=["agent"])

class AgentRequest(BaseModel):
    query: str

class AgentResponse(BaseModel):
    answer: str
    tool_calls: list[dict]
    token_usage: dict

@router.post("/run", response_model=AgentResponse)
async def run_agent_route(
    body: AgentRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Eagerly capture user data before any async operations
    user_id = current_user.id
    user_email = current_user.email

    result = await run_agent(body.query, db)

    agent_run = AgentRun(
        user_id=user_id,
        user_query=body.query,
        answer=result["answer"]
    )
    db.add(agent_run)
    await db.flush()

    for tool_call in result["tool_calls"]:
        log = ToolCallLog(
            run_id=agent_run.id,
            tool_name=tool_call["tool_name"],
            tool_input=tool_call["tool_input"],
            tool_output=tool_call["tool_output"]
        )
        db.add(log)

    await db.commit()

    background_tasks.add_task(
        deliver_webhook,
        user_email=user_email,
        query=body.query,
        answer=result["answer"],
        tool_calls=result["tool_calls"]
    )

    return AgentResponse(
        answer=result["answer"],
        tool_calls=result["tool_calls"],
        token_usage=result["token_usage"]
    )


@router.get("/history")
async def get_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy import select
    result = await db.execute(
        select(AgentRun)
        .where(AgentRun.user_id == current_user.id)
        .order_by(AgentRun.created_at.desc())
    )
    runs = result.scalars().all()
    return [
        {
            "id": str(run.id),
            "query": run.user_query,
            "answer": run.answer,
            "created_at": run.created_at.isoformat()
        }
        for run in runs
    ]
@router.post("/run/stream")
async def run_agent_stream(
    body: AgentRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.id
    user_email = current_user.email

    async def generate():
        result = await run_agent(body.query, db)

        # Stream tool calls first
        for tool_call in result["tool_calls"]:
            yield f"data: {json.dumps({'type': 'tool_call', 'data': tool_call})}\n\n"

        # Stream answer word by word
        words = result["answer"].split(" ")
        for word in words:
            yield f"data: {json.dumps({'type': 'token', 'data': word + ' '})}\n\n"

        # Stream done signal
        yield f"data: {json.dumps({'type': 'done', 'token_usage': result['token_usage']})}\n\n"

        # Persist run
        agent_run = AgentRun(
            user_id=user_id,
            user_query=body.query,
            answer=result["answer"]
        )
        db.add(agent_run)
        await db.flush()

        for tool_call in result["tool_calls"]:
            log = ToolCallLog(
                run_id=agent_run.id,
                tool_name=tool_call["tool_name"],
                tool_input=tool_call["tool_input"],
                tool_output=tool_call["tool_output"]
            )
            db.add(log)

        await db.commit()

        background_tasks.add_task(
            deliver_webhook,
            user_email=user_email,
            query=body.query,
            answer=result["answer"],
            tool_calls=result["tool_calls"]
        )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )