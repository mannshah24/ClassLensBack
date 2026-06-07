from django.contrib import admin

# Register your models here.

from .models import Student, Subject, Teacher, Department, ClassSession, SubjectFromDept, TeacherSubject, StudentEnrollment, Division, Holiday

admin.site.register(Student)
admin.site.register(Teacher)
admin.site.register(Subject)
admin.site.register(TeacherSubject)
admin.site.register(StudentEnrollment)

admin.site.register(Department)

admin.site.register(SubjectFromDept)
admin.site.register(Division)

@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('date', 'name', 'is_working_day')
    list_filter = ('is_working_day',)
    search_fields = ('name',)
