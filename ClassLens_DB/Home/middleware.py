import traceback
import json
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.tokens import AccessToken
from Home.db_logger import log_normal, log_error
from Home.models import Student, Teacher, AdminUser

class DBLoggingMiddleware(MiddlewareMixin):
    def __call__(self, request):
        from Home.db_logger import set_current_request, clear_current_request
        set_current_request(request)
        
        # Cache the request body for non-multipart requests to prevent RawPostDataException downstream
        content_type = getattr(request, 'content_type', '').lower()
        if 'multipart' not in content_type:
            try:
                content_length = int(request.META.get('CONTENT_LENGTH', 0) or 0)
                if content_length < 2 * 1024 * 1024:  # 2MB threshold
                    _ = request.body
            except Exception:
                pass
        
        try:
            return super().__call__(request)
        finally:
            clear_current_request()

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get_request_payload(self, request):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return None
        
        content_type = getattr(request, 'content_type', '').lower()
        if 'multipart/form-data' in content_type:
            try:
                data = {}
                for key, val in request.POST.items():
                    data[key] = val
                for key, val in request.FILES.items():
                    data[key] = f"<File: {val.name} ({val.size} bytes)>"
                return data
            except Exception:
                return {"note": "Unable to read multipart POST data"}
        
        try:
            body = getattr(request, 'body', b'')
            if body:
                try:
                    return json.loads(body)
                except Exception:
                    return {"raw_body": body.decode('utf-8', errors='ignore')[:1000]}
        except Exception as e:
            try:
                if request.POST:
                    return dict(request.POST.items())
            except Exception:
                pass
            return {"error": f"Payload unreadable: {str(e)}"}
        return None

    def get_actor_info(self, request):
        # 1. Try request.user first
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            actor_id = getattr(user, 'id', getattr(user, 'pk', None))
            actor_email = getattr(user, 'email', getattr(user, 'username', None))
            return actor_id, actor_email

        # 2. Extract from JWT token in the Authorization header (check both request.META and request.headers)
        auth_header = request.META.get('HTTP_AUTHORIZATION', '') or request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            try:
                token_str = auth_header.split(' ')[1]
                token = AccessToken(token_str)
                
                actor_id = token.get('user_id') or token.get('student_id') or token.get('teacher_id')
                actor_email = None
                
                if actor_id:
                    # Run fast query to get email snapshot
                    if 'student_id' in token:
                        student = Student.objects.filter(id=actor_id).only('email').first()
                        if student:
                            actor_email = student.email
                    elif 'username' in token:  # AdminUser
                        admin = AdminUser.objects.filter(id=actor_id).only('username').first()
                        if admin:
                            actor_email = admin.username
                    else:  # Teacher / Generic fallback
                        teacher = Teacher.objects.filter(id=actor_id).only('email').first()
                        if teacher:
                            actor_email = teacher.email
                
                if actor_id:
                    return actor_id, actor_email
            except Exception:
                pass

        # 3. Fallback: Parse actor from request parameters (POST/GET/JSON payload)
        # This is extremely common for teacher requests which pass teacher_id directly
        try:
            actor_id = None
            actor_email = None
            
            def find_key_value(data_dict):
                for key in ['teacher_id', 'teacherID', 'student_id', 'studentID', 'prn', 'actor_id', 'user_id']:
                    if key in data_dict:
                        val = data_dict[key]
                        if val:
                            try:
                                return int(val)
                            except ValueError:
                                pass
                return None

            actor_id = find_key_value(request.GET)
            
            if not actor_id:
                actor_id = find_key_value(request.POST)
                
            if not actor_id:
                payload = self.get_request_payload(request)
                if isinstance(payload, dict):
                    actor_id = find_key_value(payload)

            if actor_id:
                # Query Teacher first
                teacher = Teacher.objects.filter(id=actor_id).only('email').first()
                if teacher:
                    actor_email = teacher.email
                else:
                    # Query Student by ID or PRN
                    student = Student.objects.filter(id=actor_id).only('email').first()
                    if not student:
                        student = Student.objects.filter(prn=actor_id).only('email').first()
                    if student:
                        actor_email = student.email
            
            return actor_id, actor_email
        except Exception:
            pass

        return None, None

    def process_response(self, request, response):
        # Log successful state changes (status 2xx or 3xx)
        if 200 <= response.status_code < 400:
            if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                action = f"{request.method}_{request.resolver_match.url_name.upper()}" if request.resolver_match and request.resolver_match.url_name else f"{request.method}_API"
                module = request.resolver_match.app_name or request.resolver_match.view_name or 'views' if request.resolver_match else 'views'
                actor_id, actor_email = self.get_actor_info(request)
                summary = f"Request: {request.method} {request.path} completed with status {response.status_code}"
                
                log_normal(
                    module=module,
                    action=action,
                    actor_id=actor_id,
                    actor_email=actor_email,
                    request_path=request.path,
                    ip_address=self.get_client_ip(request),
                    summary=summary
                )
        return response

    def process_exception(self, request, exception):
        # Intercept exception to write to error table
        import sys
        exc_type, exc_value, exc_tb = sys.exc_info()
        traceback_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        
        module = request.resolver_match.app_name or request.resolver_match.view_name or 'views' if request.resolver_match else 'views'
        actor_id, _ = self.get_actor_info(request)
        request_payload = self.get_request_payload(request)
        
        log_error(
            module=module,
            error_type=exception.__class__.__name__,
            error_message=str(exception),
            traceback_str=traceback_str,
            request_payload=request_payload,
            actor_id=actor_id
        )
        # Return None to allow Django to perform its default exception/rollback processing
        return None
