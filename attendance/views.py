from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib import messages
from django.db.models import Count, Avg, F
from django.db.models.functions import ExtractHour, TruncDate
from django.http import HttpResponse
from .models import AttendanceLog
import csv
import json
from datetime import timedelta

def home(request):
    from .models import LibrarySystemState
    state = LibrarySystemState.get_state()
    # Pass active logs so the checkout screen can display them
    active_logs = AttendanceLog.objects.filter(status='Active').order_by('-timestamp_in')
    return render(request, 'attendance/home.html', {'active_logs': active_logs, 'is_open': state.is_open})

def checkin(request):
    from .models import LibrarySystemState
    state = LibrarySystemState.get_state()
    if not state.is_open:
        messages.error(request, "The library is currently closed. You cannot check in.")
        return redirect('home')

    if request.method == 'POST':
        identifier = request.POST.get('student_id', '').strip()
        student_name = request.POST.get('student_name', '').strip()
        force_checkin = request.POST.get('force_checkin', '')
        
        if not identifier or not student_name:
            messages.error(request, "Please enter both your Student ID and your Name.")
            return render(request, 'attendance/home.html', {
                'status': 'error',
                'active_logs': AttendanceLog.objects.filter(status='Active'),
            })

        if not identifier.isdigit() or len(identifier) != 8:
            messages.error(request, "Invalid Student ID. It must be exactly 8 digits.")
            return render(request, 'attendance/home.html', {
                'status': 'error',
                'active_logs': AttendanceLog.objects.filter(status='Active'),
            })

        # Check if already checked in with exact same ID and name (case-insensitive)
        already_active_exact = AttendanceLog.objects.filter(
            identifier=identifier, status='Active'
        ).filter(student_name__iexact=student_name).first()

        if already_active_exact:
            messages.error(request, f"{student_name}, you are already checked in!")
            return render(request, 'attendance/home.html', {
                'status': 'error',
                'active_logs': AttendanceLog.objects.filter(status='Active'),
            })

        # Check if same ID is active under a DIFFERENT name
        active_same_id = AttendanceLog.objects.filter(
            identifier=identifier, status='Active'
        ).first()

        if active_same_id and force_checkin != 'yes':
            return render(request, 'attendance/home.html', {
                'status': 'conflict',
                'conflict_name': active_same_id.student_name,
                'conflict_id': active_same_id.identifier,
                'conflict_type': 'id',
                'entered_id': identifier,
                'entered_name': student_name,
                'active_logs': AttendanceLog.objects.filter(status='Active'),
            })

        # Check if same NAME is active under a DIFFERENT ID
        active_same_name = AttendanceLog.objects.filter(
            student_name__iexact=student_name, status='Active'
        ).first()

        if active_same_name and force_checkin != 'yes':
            return render(request, 'attendance/home.html', {
                'status': 'conflict',
                'conflict_name': active_same_name.student_name,
                'conflict_id': active_same_name.identifier,
                'conflict_type': 'name',
                'entered_id': identifier,
                'entered_name': student_name,
                'active_logs': AttendanceLog.objects.filter(status='Active'),
            })

        AttendanceLog.objects.create(identifier=identifier, student_name=student_name, status='Active')
        return render(request, 'attendance/home.html', {'status': 'checkin', 'identifier': student_name})
    
    return redirect('home')

def quick_checkout(request):
    if request.method == 'POST':
        log_id = request.POST.get('log_id')
        if log_id:
            try:
                log = AttendanceLog.objects.get(id=log_id, status='Active')
                log.timestamp_out = timezone.now()
                log.status = 'Completed'
                log.save()
                return render(request, 'attendance/home.html', {'status': 'checkout', 'identifier': log.student_name or log.identifier})
            except AttendanceLog.DoesNotExist:
                messages.error(request, "Could not find that record. Please try again.")
                return render(request, 'attendance/home.html', {
                    'status': 'error',
                    'active_logs': AttendanceLog.objects.filter(status='Active'),
                })
    return redirect('home')

def dashboard_login(request):
    if request.method == 'POST':
        password = request.POST.get('password', '')
        import os
        if password == os.environ.get('LIBRARIAN_PASSWORD', 'admin123'):
            request.session['is_librarian'] = True
            return redirect('dashboard')
        else:
            messages.error(request, "Incorrect password.")
    return render(request, 'attendance/login.html')

def dashboard_logout(request):
    request.session.flush()
    messages.success(request, "You have been logged out.")
    return redirect('home')

def dashboard(request):
    if not request.session.get('is_librarian'):
        return redirect('dashboard_login')
        
    from .models import LibrarySystemState
    state = LibrarySystemState.get_state()

    if request.method == 'POST':
        if 'toggle_library' in request.POST:
            state.is_open = not state.is_open
            state.save()
            
            if not state.is_open:
                active_logs = AttendanceLog.objects.filter(status='Active')
                count = active_logs.count()
                if count > 0:
                    active_logs.update(timestamp_out=timezone.now(), status='Completed')
                    messages.success(request, f"The library has been closed. {count} active students were automatically checked out.")
                else:
                    messages.success(request, "The library has been closed.")
            else:
                messages.success(request, "The library has been opened.")
                
            return redirect('dashboard')
            
        # Handle manual checkout from dashboard
        log_id = request.POST.get('log_id')
        if log_id:
            try:
                log = AttendanceLog.objects.get(id=log_id, status='Active')
                log.timestamp_out = timezone.now()
                log.status = 'Completed'
                log.save()
                messages.success(request, f"Checked out {log.identifier}.")
            except AttendanceLog.DoesNotExist:
                pass
        return redirect('dashboard')
        
    active_logs = AttendanceLog.objects.filter(status='Active').order_by('-timestamp_in')
    historical_logs = AttendanceLog.objects.filter(status='Completed').order_by('-timestamp_in')[:100]

    now = timezone.now()
    today = now.date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    total_today = AttendanceLog.objects.filter(timestamp_in__date=today).count()
    currently_inside = active_logs.count()
    total_this_week = AttendanceLog.objects.filter(timestamp_in__date__gte=week_ago).count()
    total_this_month = AttendanceLog.objects.filter(timestamp_in__date__gte=month_ago).count()

    # Average daily visitors (last 30 days)
    daily_counts = (
        AttendanceLog.objects
        .filter(timestamp_in__date__gte=month_ago)
        .annotate(day=TruncDate('timestamp_in'))
        .values('day')
        .annotate(count=Count('id'))
    )
    avg_daily = round(sum(d['count'] for d in daily_counts) / len(daily_counts), 1) if daily_counts else 0

    # Average time spent
    from django.db.models import ExpressionWrapper, DurationField
    avg_duration = (
        AttendanceLog.objects.filter(
            status='Completed', timestamp_out__isnull=False, timestamp_in__date__gte=month_ago,
        )
        .annotate(duration=ExpressionWrapper(F('timestamp_out') - F('timestamp_in'), output_field=DurationField()))
        .aggregate(avg=Avg('duration'))
    )['avg']
    if avg_duration:
        avg_seconds = avg_duration.total_seconds()
        avg_hours = int(avg_seconds // 3600)
        avg_minutes = int((avg_seconds % 3600) // 60)
        avg_time_spent = f"{avg_hours}h {avg_minutes}m" if avg_hours > 0 else f"{avg_minutes} min"
    else:
        avg_time_spent = "N/A"

    # Peak hour today
    hourly_today = (
        AttendanceLog.objects.filter(timestamp_in__date=today)
        .annotate(hour=ExtractHour('timestamp_in'))
        .values('hour').annotate(count=Count('id')).order_by('-count')
    )
    if hourly_today:
        ps = hourly_today[0]['hour']
        peak_hour = f"{ps % 12 or 12}:00 {'AM' if ps < 12 else 'PM'} - {(ps+1) % 12 or 12}:00 {'AM' if ps+1 < 12 else 'PM'}"
    else:
        peak_hour = "N/A"

    # Chart: Visitors per day (last 7 days)
    daily_labels, daily_data = [], []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        daily_labels.append(day.strftime('%a %d'))
        daily_data.append(AttendanceLog.objects.filter(timestamp_in__date=day).count())

    # Chart: Hourly traffic today
    hourly_labels = [f"{h % 12 or 12} {'AM' if h < 12 else 'PM'}" for h in range(24)]
    hourly_counts = dict(
        AttendanceLog.objects.filter(timestamp_in__date=today)
        .annotate(hour=ExtractHour('timestamp_in'))
        .values('hour').annotate(count=Count('id'))
        .values_list('hour', 'count')
    )
    hourly_data = [hourly_counts.get(h, 0) for h in range(24)]

    # Chart: Top 10 visitors
    top_visitors = AttendanceLog.objects.values('student_name').annotate(visits=Count('id')).order_by('-visits')[:10]
    top_labels = [v['student_name'] or 'Unknown' for v in top_visitors]
    top_data = [v['visits'] for v in top_visitors]

    # Chart: Day of week breakdown
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    dow_counts = dict(
        AttendanceLog.objects.filter(timestamp_in__date__gte=month_ago)
        .values('timestamp_in__iso_week_day')
        .annotate(count=Count('id'))
        .values_list('timestamp_in__iso_week_day', 'count')
    )
    dow_data = [dow_counts.get(i + 1, 0) for i in range(7)]

    # Chart: Avg duration by day
    from django.db.models import ExpressionWrapper, DurationField
    avg_by_dow = dict(
        AttendanceLog.objects.filter(
            status='Completed', timestamp_out__isnull=False, timestamp_in__date__gte=month_ago
        )
        .annotate(
            dow=F('timestamp_in__iso_week_day'),
            duration=ExpressionWrapper(F('timestamp_out') - F('timestamp_in'), output_field=DurationField())
        )
        .values('dow')
        .annotate(avg_dur=Avg('duration'))
        .values_list('dow', 'avg_dur')
    )
    avg_duration_by_day = [
        round(avg_by_dow[i + 1].total_seconds() / 60, 1) if avg_by_dow.get(i + 1) else 0
        for i in range(7)
    ]

    context = {
        'is_open': state.is_open,
        'active_logs': active_logs,
        'historical_logs': historical_logs,
        'total_today': total_today,
        'currently_inside': currently_inside,
        'total_this_week': total_this_week,
        'total_this_month': total_this_month,
        'avg_daily': avg_daily,
        'avg_time_spent': avg_time_spent,
        'peak_hour': peak_hour,
        'daily_labels': daily_labels,
        'daily_data': daily_data,
        'hourly_labels': hourly_labels,
        'hourly_data': hourly_data,
        'top_labels': top_labels,
        'top_data': top_data,
        'dow_labels': day_names,
        'dow_data': dow_data,
        'avg_duration_labels': day_names,
        'avg_duration_data': avg_duration_by_day,
    }
    return render(request, 'attendance/dashboard.html', context)



def export_csv(request):
    if not request.session.get('is_librarian'):
        return redirect('dashboard_login')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="library_logs_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Log ID', 'Student ID', 'Student Name', 'Time In', 'Time Out', 'Status'])

    logs = AttendanceLog.objects.all().order_by('-timestamp_in')
    for log in logs:
        writer.writerow([
            log.id,
            log.identifier,
            log.student_name,
            log.timestamp_in.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp_in else '',
            log.timestamp_out.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp_out else '',
            log.status,
        ])

    return response
