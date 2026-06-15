from rest_framework import serializers
from .models import Department,Subject,AdminUser,Holiday,TimetableTemplate,DailySession

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id','name']

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id','code','name']

class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = ['id', 'date', 'name', 'is_working_day']


class TimetableTemplateSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    division_name = serializers.CharField(source='division.name', read_only=True)
    default_teacher_name = serializers.CharField(source='default_teacher.name', read_only=True)

    class Meta:
        model = TimetableTemplate
        fields = '__all__'


class DailySessionSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    subject_code = serializers.CharField(source='subject.code', read_only=True)
    division_name = serializers.CharField(source='division.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    proxy_teacher_name = serializers.CharField(source='proxy_teacher.name', read_only=True)
    attendance_marked = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = DailySession
        fields = '__all__'

    def get_attendance_marked(self, obj):
        from .models import AttendanceRecord
        return AttendanceRecord.objects.filter(
            class_session__subject=obj.subject,
            student__division=obj.division,
            class_session__class_datetime__date=obj.date
        ).exists()

    def get_status(self, obj):
        if obj.is_cancelled:
            return "Canceled"
        from .models import AttendanceRecord
        if AttendanceRecord.objects.filter(
            class_session__subject=obj.subject,
            student__division=obj.division,
            class_session__class_datetime__date=obj.date
        ).exists():
            return "Completed"
        return "Scheduled"



