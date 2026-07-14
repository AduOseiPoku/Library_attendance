from django.contrib import admin
from .models import AttendanceLog, LibrarySystemState

@admin.register(AttendanceLog)
class AttendanceLogAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'student_name', 'timestamp_in', 'timestamp_out', 'status')
    list_filter = ('status', 'timestamp_in')
    search_fields = ('identifier', 'student_name')
    ordering = ('-timestamp_in',)

@admin.register(LibrarySystemState)
class LibrarySystemStateAdmin(admin.ModelAdmin):
    list_display = ('id', 'is_open')
