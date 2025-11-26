from celery import shared_task
from .helper import Helper
from .models import AnalysisTask
from django.utils import timezone
from django.core.cache import cache
import logging
import traceback

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def run_dynamic_analysis(self, task_id):
    """
    Background task for dynamic analysis
    
    Args:
        self: Celery task instance (bind=True)
        task_id: ID of AnalysisTask model instance
    
    Returns:
        dict: Status and results
    """
    logger.info(f"🚀 Worker {self.request.hostname} starting task {task_id}")
    
    try:
        # Get task from database
        task = AnalysisTask.objects.get(id=task_id)
        
        # Update status to running
        task.status = 'running'
        task.started_at = timezone.now()
        task.worker_id = self.request.hostname
        task.save()
        
        logger.info(f"📦 Analyzing {task.package_name}@{task.package_version} ({task.ecosystem})")
        
        # Check cache first
        cache_key = f"analysis_{task.ecosystem}_{task.package_name}_{task.package_version}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            logger.info(f"✅ Using cached result for {task.package_name}@{task.package_version}")
            task.status = 'completed'
            task.completed_at = timezone.now()
            task.duration_seconds = 0.1  # Cache hit
            task.result = cached_result
            task.save()
            
            return {
                'status': 'success',
                'task_id': task_id,
                'cached': True
            }
        
        # Run analysis
        start_time = timezone.now()
        
        results = Helper.run_package_analysis(
            package_name=task.package_name,
            package_version=task.package_version,
            ecosystem=task.ecosystem
        )
        
        # Calculate duration
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()
        
        # Save to cache (7 days)
        cache.set(cache_key, results, timeout=7*24*60*60)
        
        # Save results to database
        task.status = 'completed'
        task.completed_at = end_time
        task.duration_seconds = duration
        task.result = results
        task.save()
        
        logger.info(f"✅ Task {task_id} completed in {duration:.2f}s by {self.request.hostname}")
        
        return {
            'status': 'success',
            'task_id': task_id,
            'duration': duration,
            'cached': False
        }
        
    except Exception as e:
        logger.error(f"❌ Task {task_id} failed: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Update task status
        try:
            task = AnalysisTask.objects.get(id=task_id)
            task.status = 'failed'
            task.completed_at = timezone.now()
            task.error_message = str(e)
            task.error_traceback = traceback.format_exc()
            task.save()
        except Exception as save_error:
            logger.error(f"Failed to save error state: {save_error}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            retry_countdown = 60 * (2 ** self.request.retries)
            logger.info(f"🔄 Retrying task {task_id} in {retry_countdown}s (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e, countdown=retry_countdown)
        else:
            logger.error(f"💀 Task {task_id} failed permanently after {self.max_retries} retries")
            raise

@shared_task
def cleanup_old_tasks():
    """
    Periodic task to clean up old completed/failed tasks
    Keeps tasks for 7 days
    """
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=7)
    
    # Delete old completed tasks
    deleted_completed = AnalysisTask.objects.filter(
        status='completed',
        completed_at__lt=cutoff_date
    ).delete()[0]
    
    # Delete old failed tasks
    deleted_failed = AnalysisTask.objects.filter(
        status='failed',
        completed_at__lt=cutoff_date
    ).delete()[0]
    
    total_deleted = deleted_completed + deleted_failed
    
    logger.info(f"🧹 Cleaned up {total_deleted} old tasks ({deleted_completed} completed, {deleted_failed} failed)")
    
    return {
        'deleted_completed': deleted_completed,
        'deleted_failed': deleted_failed,
        'total': total_deleted
    }

@shared_task
def test_task():
    """Simple test task to verify Celery is working"""
    logger.info("✅ Celery is working!")
    return "Celery is working!"
