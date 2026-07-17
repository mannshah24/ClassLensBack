# # Home/authentication.py

# from rest_framework_simplejwt.authentication import JWTAuthentication
# from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
# from .models import AdminUser

# class CustomAdminAuthentication(JWTAuthentication):
#     def get_user(self, validated_token):
#         print("--- Custom Auth is Running ---") # Debug Print
        
#         try:
#             # 1. Check if user_id is in the token
#             user_id = validated_token.get('user_id')
#             print(f"Token User ID: {user_id}") # Debug Print
            
#             if not user_id:
#                 raise InvalidToken('Token is missing user_id')

#             # 2. Try to find the user in YOUR custom table
#             user = AdminUser.objects.get(id=user_id)
#             print(f"Found User: {user.username}") # Debug Print
#             return user
            
#         except AdminUser.DoesNotExist:
#             print("User does not exist in AdminUser table") # Debug Print
#             raise AuthenticationFailed('User not found', code='user_not_found')
#         except Exception as e:
#             print(f"Auth Error: {str(e)}") # Debug Print
#             raise InvalidToken('Token validation error')



# Home/authentication.py

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from .models import AdminUser, Teacher, Student

class CustomAdminAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        print("--- Custom Auth is Running ---")
        print(f"Full token payload: {validated_token}")
        
        try:
            user_id = validated_token.get('user_id')
            print(f"Token User ID: {user_id}")
            
            if not user_id:
                print("No user_id in token")
                raise InvalidToken('Token is missing user_id')

            user = AdminUser.objects.get(id=user_id)
            print(f"Found User: {user.username}")
            return user
            
        except AdminUser.DoesNotExist:
            print(f"User with id {user_id} does not exist in AdminUser table")
            raise AuthenticationFailed('User not found', code='user_not_found')
        except Exception as e:
            print(f"Auth Error: {str(e)}")
            raise InvalidToken('Token validation error')

class ClassLensJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        try:
            header = self.get_header(request)
            if header is None:
                print("--- ClassLensJWTAuth: No header found ---")
                return None
            raw_token = self.get_raw_token(header)
            if raw_token is None:
                print("--- ClassLensJWTAuth: No raw token found ---")
                return None
                
            # Decode token safely for checking
            token_str = ""
            try:
                token_str = raw_token.decode('utf-8')
            except Exception:
                token_str = str(raw_token)
                
            if not token_str or token_str.strip() == "" or token_str.strip().lower() == "null" or token_str.strip().lower() == "bearer":
                print("--- ClassLensJWTAuth: Empty or invalid token string, skipping auth ---")
                return None

            print(f"--- ClassLensJWTAuth: Raw token is {raw_token} ---")
            validated_token = self.get_validated_token(raw_token)
            print(f"--- ClassLensJWTAuth: Validated token payload: {validated_token} ---")
            user = self.get_user(validated_token)
            print(f"--- ClassLensJWTAuth: Resolved user: {user} ---")
            return user, validated_token
        except Exception as e:
            print(f"--- ClassLensJWTAuth Exception: {str(e)} ---")
            if 'export' in request.path:
                print(f"--- ClassLensJWTAuth Exception on export path (bypassing): {str(e)} ---")
                return None
            raise e

    def get_user(self, validated_token):
        # 1. Try Teacher if teacher_id exists in token
        teacher_id = validated_token.get('teacher_id')
        print(f"--- ClassLensJWTAuth get_user: teacher_id={teacher_id} ---")
        if teacher_id:
            try:
                t = Teacher.objects.get(id=teacher_id)
                print(f"--- ClassLensJWTAuth get_user: Found teacher {t} ---")
                return t
            except Teacher.DoesNotExist:
                print("--- ClassLensJWTAuth get_user: Teacher not found ---")
                pass

        # 2. Try Student if student_id exists in token
        student_id = validated_token.get('student_id')
        print(f"--- ClassLensJWTAuth get_user: student_id={student_id} ---")
        if student_id:
            try:
                s = Student.objects.get(id=student_id)
                print(f"--- ClassLensJWTAuth get_user: Found student {s} ---")
                return s
            except Student.DoesNotExist:
                print("--- ClassLensJWTAuth get_user: Student not found ---")
                pass

        user_id = validated_token.get('user_id')
        print(f"--- ClassLensJWTAuth get_user: user_id={user_id} ---")
        
        # 3. Try AdminUser
        if user_id:
            try:
                a = AdminUser.objects.get(id=user_id)
                print(f"--- ClassLensJWTAuth get_user: Found admin {a} ---")
                return a
            except AdminUser.DoesNotExist:
                print("--- ClassLensJWTAuth get_user: AdminUser not found ---")
                pass

        # Fallback to standard Django User if user_id is provided
        if user_id:
            try:
                u = super().get_user(validated_token)
                print(f"--- ClassLensJWTAuth get_user: Found super user {u} ---")
                return u
            except Exception as super_err:
                print(f"--- ClassLensJWTAuth get_user: super.get_user error {super_err} ---")
                pass

        raise AuthenticationFailed('User not found', code='user_not_found')