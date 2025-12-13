# app/services/worker_service.py Transpiler worker service
import asyncio
import logging
import traceback
from datetime import datetime
from typing import Dict, Any
import hashlib
import httpx

from ...app.db.session import SessionLocal
from ...app.models.transpiler_job import TranspilerJob, JobStatus
from ...app.models.user import User
from ...app.models.subscription import Subscription
from ...app.services.queue_services import queue_service
from ...app.services.transpiler_service import transpiler_service

logger = logging.getLogger(__name__)


class WorkerService:
    def __init__(self):
        self.queue_name = "transpiler_jobs"
        self.running = False

    async def start(self):
        """Start the worker"""
        self.running = True
        logger.info("Transpiler worker started")

        while self.running:
            try:
                await self.process_next_job()
                await asyncio.sleep(0.1)  # Small delay to prevent CPU spinning
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)

    def stop(self):
        """Stop the worker"""
        self.running = False
        logger.info("Transpiler worker stopped")

    async def process_next_job(self):
        """Process next job from queue"""
        job_data = queue_service.dequeue(self.queue_name)
        if not job_data:
            return

        job_id = job_data.get("job_id")
        if not job_id:
            return

        db = SessionLocal()
        try:
            # Get job from database
            job = db.query(TranspilerJob).filter(TranspilerJob.id == job_id).first()
            if not job:
                logger.warning(f"Job {job_id} not found in database")
                return

            # Skip if already completed or cancelled
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                logger.info(f"Job {job_id} already in final state: {job.status}")
                return

            # Update job status to processing
            job.status = JobStatus.PROCESSING
            job.started_at = datetime.utcnow()
            db.commit()

            logger.info(f"Processing job {job_id} for user {job.user_id}")

            # Process the job
            start_time = datetime.now()

            result = await transpiler_service.transpile_and_execute(
                code=job.code,
                language=job.language,
                input_data=job.input_data,
                timeout=job.timeout_seconds
            )

            # Calculate execution time
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            # Update job with results
            job.transpiled_code = result.get("transpiled_code")
            job.execution_output = result.get("output")
            job.errors = result.get("errors")
            job.success = result.get("success", False)
            job.execution_time_ms = int(execution_time * 1000)
            job.status = JobStatus.COMPLETED if job.success else JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.logs = result.get("logs", "")

            db.commit()

            logger.info(f"Job {job_id} completed with status: {job.status}")

            # Update billing metrics if job was successful
            if job.success:
                try:
                    user = db.query(User).filter(User.id == job.user_id).first()
                    if user:
                        user.total_code_executions += 1
                        user.last_execution_at = datetime.utcnow()

                        # Update active subscription metrics
                        active_subscription = db.query(Subscription).filter(
                            Subscription.user_id == job.user_id,
                            Subscription.status == "active"
                        ).first()
                        if active_subscription:
                            active_subscription.executions_this_month += 1
                            active_subscription.total_executions += 1

                        db.commit()
                        logger.info(f"Updated billing metrics for user {job.user_id}")
                except Exception as e:
                    logger.error(f"Failed to update billing metrics: {e}")
                    db.rollback()

            # Trigger webhook if configured
            try:
                user = db.query(User).filter(User.id == job.user_id).first()
                if user and user.webhook_url:
                    webhook_data = {
                        "job_id": job.id,
                        "user_id": job.user_id,
                        "status": job.status.value,
                        "success": job.success,
                        "language": job.language,
                        "execution_time_ms": job.execution_time_ms,
                        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                        "output": job.execution_output,
                        "errors": job.errors,
                        "transpiled_code": job.transpiled_code
                    }

                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.post(user.webhook_url, json=webhook_data)
                        if response.status_code == 200:
                            logger.info(f"Webhook sent successfully to {user.webhook_url}")
                        else:
                            logger.warning(f"Webhook failed with status {response.status_code}: {response.text}")
            except Exception as e:
                logger.error(f"Failed to send webhook: {e}")
        except Exception as e:
            logger.error(f"Failed to process job {job_id}: {e}")
            logger.error(traceback.format_exc())

            # Mark job as failed
            try:
                job.status = JobStatus.FAILED
                job.errors = str(e)
                job.completed_at = datetime.utcnow()
                db.commit()
            except:
                db.rollback()

        finally:
            db.close()


# Global worker instance
worker_service = WorkerService()