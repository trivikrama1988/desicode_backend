# app/api/v1/transpiler.py
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, Query
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import hashlib
import uuid
from enum import Enum

from ...security import get_current_user
from ....db.session import get_db
from ....models.user import User
from ....models.subscription import Subscription, Plan, SubscriptionStatus
from ....models.transpiler_job import TranspilerJob, JobStatus
from ....services.queue_service import queue_service
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

router = APIRouter()


# Define supported languages
class LanguageCode(str, Enum):
    ASSAMESE = "assamese"
    BENGALI = "bengali"
    BODO = "bodo"
    MANIPURI = "manipuri"
    KHASI = "khasi"
    GARO = "garo"
    MIZO = "mizo"


# Request Models
class TranspileRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=50000)
    language: LanguageCode
    input_data: Optional[str] = Field(None, max_length=5000)
    timeout: int = Field(default=5, ge=1, le=120)
    sync: bool = Field(default=False)
    idempotency_key: Optional[str] = Field(None, max_length=100)

    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        forbidden_patterns = [
            '__import__', 'eval(', 'exec(', 'compile(',
            'import os', 'import sys', 'import subprocess',
            'open(__file__)', 'rm -rf', 'shutdown'
        ]
        for pattern in forbidden_patterns:
            if pattern in v.lower():
                raise ValueError(f'Code contains restricted operation: {pattern}')
        return v


# Response Models
class JobResult(BaseModel):
    transpiled_code: Optional[str]
    execution_output: Optional[str]
    errors: Optional[str]
    logs: Optional[str]


class JobData(BaseModel):
    job_id: str
    status: JobStatus
    submitted_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    language: str
    timeout: int
    execution_time_ms: Optional[int] = None
    result: Optional[JobResult] = None
    quota_used: int = 1


class StandardResponse(BaseModel):
    ok: bool = True
    data: JobData


class ErrorResponse(BaseModel):
    ok: bool = False
    error: Dict[str, Any]


# Helper Functions
async def check_subscription_and_quota(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Check user has active subscription and quota"""
    user_id = current_user.id

    # Calculate quota for current month
    today = datetime.now(timezone.utc)
    first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Count jobs this month
    jobs_this_month = db.query(func.count(TranspilerJob.id)).filter(
        and_(
            TranspilerJob.user_id == user_id,
            TranspilerJob.submitted_at >= first_day_of_month
        )
    ).scalar() or 0

    # Check active subscription
    subscription = db.query(Subscription).filter(
        and_(
            Subscription.user_id == user_id,
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.current_period_end > datetime.now(timezone.utc)
        )
    ).first()

    if subscription:
        # User has active subscription - use plan quota
        plan = db.query(Plan).filter(Plan.id == subscription.plan_id).first()
        if not plan:
            raise HTTPException(status_code=500, detail="Plan not found")

        # Get monthly quota based on plan
        quota_map = {
            "free": 10,
            "pro": 100,
            "team": 1000,
            "campus": 10000
        }

        monthly_quota = quota_map.get(plan.name.lower(), 100)
        plan_type = plan.name.lower()
        plan_name = plan.name
        subscription_id = subscription.id
    else:
        # User doesn't have subscription - use free tier quota
        monthly_quota = 5  # Free users get 5 executions per month
        plan_type = "free"
        plan_name = "Free Tier"
        subscription_id = None

    quota_remaining = monthly_quota - jobs_this_month

    if quota_remaining <= 0:
        if subscription:
            raise HTTPException(
                status_code=429,
                detail=f"Monthly execution quota exceeded ({monthly_quota} executions). Please upgrade your plan or wait until next month."
            )
        else:
            raise HTTPException(
                status_code=429,
                detail=f"Monthly execution quota exceeded ({monthly_quota} executions). Please subscribe to a plan for more executions."
            )

    return {
        "user_id": user_id,
        "subscription_id": subscription_id,
        "plan_type": plan_type,
        "plan_name": plan_name,
        "monthly_quota": monthly_quota,
        "quota_remaining": quota_remaining,
        "executions_this_month": jobs_this_month
    }


# API Endpoints
@router.post("/", response_model=StandardResponse, status_code=202)
async def create_transpiler_job(
        request: TranspileRequest,
        background_tasks: BackgroundTasks,
        subscription_info: dict = Depends(check_subscription_and_quota),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        http_request: Request = None
):
    """
    Create a transpiler job

    - If sync=true and code is small, returns result immediately
    - Otherwise queues job and returns 202 with job ID
    - Supports idempotency keys
    """
    user_id = current_user.id
    code_hash = hashlib.md5(request.code.encode()).hexdigest()

    # Check idempotency key
    if request.idempotency_key:
        existing_job = db.query(TranspilerJob).filter(
            and_(
                TranspilerJob.user_id == user_id,
                TranspilerJob.idempotency_key == request.idempotency_key
            )
        ).first()

        if existing_job:
            return StandardResponse(
                ok=True,
                data=JobData(
                    job_id=existing_job.id,
                    status=existing_job.status,
                    submitted_at=existing_job.submitted_at,
                    started_at=existing_job.started_at,
                    completed_at=existing_job.completed_at,
                    language=existing_job.language,
                    timeout=existing_job.timeout_seconds,
                    execution_time_ms=existing_job.execution_time_ms,
                    result=JobResult(
                        transpiled_code=existing_job.transpiled_code,
                        execution_output=existing_job.execution_output,
                        errors=existing_job.errors,
                        logs=existing_job.logs
                    ) if existing_job.status == JobStatus.COMPLETED else None,
                    quota_used=existing_job.quota_used
                )
            )

    # Create job record
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    job = TranspilerJob(
        id=job_id,
        user_id=user_id,
        language=request.language,
        code=request.code,
        code_hash=code_hash,
        input_data=request.input_data,
        timeout_seconds=request.timeout,
        idempotency_key=request.idempotency_key,
        ip_address=http_request.client.host if http_request and http_request.client else None,
        user_agent=http_request.headers.get("user-agent") if http_request else None,
        status=JobStatus.QUEUED,
        submitted_at=datetime.utcnow()
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    # For synchronous requests with small code
    if request.sync and len(request.code) < 1000 and request.timeout <= 5:
        from app.services.transpiler_service import transpiler_service

        try:
            # Process immediately
            job.status = JobStatus.PROCESSING
            job.started_at = datetime.utcnow()
            db.commit()

            start_time = datetime.now()
            result = await transpiler_service.transpile_and_execute(
                code=request.code,
                language=request.language,
                input_data=request.input_data,
                timeout=request.timeout
            )
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            # Update job
            job.transpiled_code = result.get("transpiled_code")
            job.execution_output = result.get("output")
            job.errors = result.get("errors")
            job.success = result.get("success", False)
            job.execution_time_ms = int(execution_time * 1000)
            job.status = JobStatus.COMPLETED if job.success else JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.logs = result.get("logs", "")

            db.commit()

            return StandardResponse(
                ok=True,
                data=JobData(
                    job_id=job.id,
                    status=job.status,
                    submitted_at=job.submitted_at,
                    started_at=job.started_at,
                    completed_at=job.completed_at,
                    language=job.language,
                    timeout=job.timeout_seconds,
                    execution_time_ms=job.execution_time_ms,
                    result=JobResult(
                        transpiled_code=job.transpiled_code,
                        execution_output=job.execution_output,
                        errors=job.errors,
                        logs=job.logs
                    ),
                    quota_used=job.quota_used
                )
            )

        except Exception as e:
            # Fall back to async
            pass

    # Queue for async processing
    queue_service.enqueue("transpiler_jobs", {
        "job_id": job_id,
        "user_id": user_id,
        "language": request.language,
        "timeout": request.timeout,
        "timestamp": datetime.utcnow().isoformat()
    })

    return StandardResponse(
        ok=True,
        data=JobData(
            job_id=job.id,
            status=job.status,
            submitted_at=job.submitted_at,
            language=job.language,
            timeout=job.timeout_seconds,
            quota_used=job.quota_used
        )
    )


@router.get("/{job_id}", response_model=StandardResponse)
async def get_job_status(
        job_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Get job status and results"""
    job = db.query(TranspilerJob).filter(TranspilerJob.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Authorization
    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this job")

    result = None
    if job.status == JobStatus.COMPLETED:
        result = JobResult(
            transpiled_code=job.transpiled_code,
            execution_output=job.execution_output,
            errors=job.errors,
            logs=job.logs
        )

    return StandardResponse(
        ok=True,
        data=JobData(
            job_id=job.id,
            status=job.status,
            submitted_at=job.submitted_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            language=job.language,
            timeout=job.timeout_seconds,
            execution_time_ms=job.execution_time_ms,
            result=result,
            quota_used=job.quota_used
        )
    )


@router.post("/{job_id}/cancel", response_model=StandardResponse)
async def cancel_job(
        job_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Cancel a pending job"""
    job = db.query(TranspilerJob).filter(TranspilerJob.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Authorization
    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this job")

    # Only allow cancellation of queued or processing jobs
    if job.status not in [JobStatus.QUEUED, JobStatus.PROCESSING]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job with status: {job.status}"
        )

    job.status = JobStatus.CANCELLED
    job.completed_at = datetime.utcnow()
    db.commit()

    return StandardResponse(
        ok=True,
        data=JobData(
            job_id=job.id,
            status=job.status,
            submitted_at=job.submitted_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            language=job.language,
            timeout=job.timeout_seconds,
            quota_used=job.quota_used
        )
    )


@router.get("/", response_model=Dict[str, Any])
async def list_user_jobs(
        skip: int = Query(0, ge=0),
        limit: int = Query(20, ge=1, le=100),
        status: Optional[JobStatus] = None,
        language: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """List user's transpiler jobs"""
    query = db.query(TranspilerJob).filter(TranspilerJob.user_id == current_user.id)

    if status:
        query = query.filter(TranspilerJob.status == status)
    if language:
        query = query.filter(TranspilerJob.language == language)

    total = query.count()
    jobs = query.order_by(TranspilerJob.submitted_at.desc()).offset(skip).limit(limit).all()

    job_list = []
    for job in jobs:
        job_data = {
            "job_id": job.id,
            "language": job.language,
            "status": job.status,
            "submitted_at": job.submitted_at.isoformat() if job.submitted_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "success": job.success,
            "execution_time_ms": job.execution_time_ms,
            "quota_used": job.quota_used
        }

        if job.status == JobStatus.COMPLETED:
            job_data["result_preview"] = {
                "output_preview": (job.execution_output or "")[:100] + (
                    "..." if len(job.execution_output or "") > 100 else ""),
                "has_errors": bool(job.errors)
            }

        job_list.append(job_data)

    return {
        "ok": True,
        "data": {
            "jobs": job_list,
            "total": total,
            "skip": skip,
            "limit": limit,
            "has_more": (skip + limit) < total
        }
    }


# Modern JSON-based endpoint
@router.post("/run", response_model=StandardResponse)
async def run_code(
        request: TranspileRequest,
        background_tasks: BackgroundTasks,
        subscription_info: dict = Depends(check_subscription_and_quota),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        http_request: Request = None
):
    """
    Execute code with JSON request body
    """
    # Force sync for immediate execution in tests
    request.sync = True

    return await create_transpiler_job(
        request=request,
        background_tasks=background_tasks,
        subscription_info=subscription_info,
        db=db,
        current_user=current_user,
        http_request=http_request
    )


@router.get("/run/quota", response_model=Dict[str, Any])
async def get_execution_quota(
        subscription_info: dict = Depends(check_subscription_and_quota),
        db: Session = Depends(get_db)
):
    """Get user's remaining execution quota"""
    user_id = subscription_info["user_id"]

    # Calculate usage for current month
    today = datetime.utcnow()
    first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Get job statistics
    job_stats = db.query(
        func.count(TranspilerJob.id),
        func.sum(func.cast(TranspilerJob.success, func.Integer))
    ).filter(
        and_(
            TranspilerJob.user_id == user_id,
            TranspilerJob.submitted_at >= first_day_of_month
        )
    ).first()

    total_jobs = job_stats[0] or 0
    successful_jobs = job_stats[1] or 0

    # Get active subscription
    subscription = db.query(Subscription).filter(
        and_(
            Subscription.user_id == user_id,
            Subscription.status == SubscriptionStatus.ACTIVE
        )
    ).first()

    plan = db.query(Plan).filter(Plan.id == subscription.plan_id).first() if subscription else None

    return {
        "ok": True,
        "data": {
            "user_id": user_id,
            "plan_name": subscription_info["plan_name"],
            "plan_type": subscription_info["plan_type"],
            "monthly_quota": subscription_info["monthly_quota"],
            "quota_remaining": subscription_info["quota_remaining"],
            "quota_used": subscription_info["monthly_quota"] - subscription_info["quota_remaining"],
            "jobs_this_month": total_jobs,
            "successful_jobs": successful_jobs,
            "success_rate": round((successful_jobs / total_jobs * 100) if total_jobs > 0 else 0, 2),
            "quota_reset_date": (first_day_of_month + timedelta(days=32)).replace(day=1).isoformat(),
            "subscription_status": "active" if subscription else "free",
            "subscription_end_date": subscription.current_period_end.isoformat() if subscription and subscription.current_period_end else None
        }
    }


@router.get("/run/supported-languages", response_model=Dict[str, Any])
async def get_supported_languages():
    """Get all supported programming languages"""
    examples = {
        "assamese": {
            "code": '# নমস্কাৰ পৃথিৱী\nপ্ৰিন্ট("নমস্কাৰ পৃথিৱী!")\nপ্ৰিন্ট("স্বাগতম অসমীয়া প্ৰগ্ৰামিং ভাষালৈ")',
            "description": "Assamese programming language"
        },
        "bengali": {
            "code": '# বাংলা প্রোগ্রামিং\nপ্রিন্ট("ওহে বিশ্ব!")\nপ্রিন্ট("বাংলা প্রোগ্রামিং ভাষায় স্বাগতম")',
            "description": "Bengali programming language"
        },
        "bodo": {
            "code": '# बोडो प्रोग्रामिंग\nprint("मोगो बिसोर!")\nprint("बोडो प्रोग्रामिंग भाषायाव थांखो हो")',
            "description": "Bodo programming language"
        },
        "manipuri": {
            "code": '# মণিপুরী প্রোগ্রামিং\nprint("হেল্লো ওয়ার্ল্ড!")\nprint("মণিপুরী প্রোগ্রামিং ভাষাত স্বাগতম")',
            "description": "Manipuri (Meitei) programming language"
        },
        "khasi": {
            "code": '# Khasi Programming\nprint("Hello World!")\nprint("Welcome to Khasi Programming")',
            "description": "Khasi programming language"
        },
        "garo": {
            "code": '# Garo Programming\nprint("Hello World!")\nprint("Welcome to Garo Programming")',
            "description": "Garo programming language"
        },
        "mizo": {
            "code": '# Mizo Programming\nprint("Hello World!")\nprint("Mizo Programming ah chibai buk rawh")',
            "description": "Mizo programming language"
        }
    }

    extensions = {
        "assamese": ".aspy",
        "bengali": ".bepy",
        "bodo": ".bopy",
        "manipuri": ".mpy",
        "khasi": ".kpy",
        "garo": ".gpy",
        "mizo": ".mzpy"
    }

    return {
        "ok": True,
        "data": {
            "languages": [{"code": lang.value, "name": lang.value.title()} for lang in LanguageCode],
            "extensions": {lang: ext for lang, ext in extensions.items()},
            "count": len(LanguageCode),
            "examples": examples
        }
    }


@router.get("/run/history", response_model=Dict[str, Any])
async def get_execution_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page")
):
    """Get user's code execution history"""
    try:
        from app.models.code_execution import CodeExecution
        
        # Calculate offset for pagination
        offset = (page - 1) * limit
        
        # Get total count
        total_count = db.query(CodeExecution).filter(
            CodeExecution.user_id == current_user.id
        ).count()
        
        # Get paginated history
        executions = db.query(CodeExecution).filter(
            CodeExecution.user_id == current_user.id
        ).order_by(CodeExecution.created_at.desc()).offset(offset).limit(limit).all()
        
        # Format the response
        history_items = []
        for execution in executions:
            history_items.append({
                "execution_id": execution.id,
                "language": execution.language,
                "success": execution.success,
                "execution_time_ms": execution.execution_time_ms,
                "error_message": execution.error_message,
                "created_at": execution.created_at.isoformat() if execution.created_at else None
            })
        
        return {
            "ok": True,
            "data": {
                "history": history_items,
                "total": total_count,
                "page": page,
                "limit": limit,
                "total_pages": (total_count + limit - 1) // limit
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get execution history: {str(e)}"
        )
