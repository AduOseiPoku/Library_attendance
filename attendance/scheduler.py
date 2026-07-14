import os
from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone

def close_library():
    from .models import AttendanceLog, LibrarySystemState
    
    # 1. Check out all active students
    active_logs = AttendanceLog.objects.filter(status='Active')
    now = timezone.now()
    active_logs.update(timestamp_out=now, status='Completed')
    
    # 2. Close the library
    state = LibrarySystemState.get_state()
    state.is_open = False
    state.save()
    print(f"[{now}] Auto-checkout completed. Library is now closed.")

def start_scheduler():
    # In Django runserver, the app loads twice. This prevents the scheduler from running twice.
    if os.environ.get('RUN_MAIN', None) != 'true':
        return

    scheduler = BackgroundScheduler()
    
    # Add the daily 5:00 PM job (17:00)
    scheduler.add_job(
        close_library,
        'cron',
        hour=17,
        minute=0,
        id='close_library_job',
        replace_existing=True
    )
    
    scheduler.start()
