import traceback
import sys

# Save the original print_exc
_original_print_exc = traceback.print_exc

def patched_print_exc(limit=None, file=None, chain=True):
    # 1. Print exception to console (original behavior)
    _original_print_exc(limit, file, chain)
    
    # 2. Log to error table
    try:
        exc_type, exc_value, exc_tb = sys.exc_info()
        if exc_value:
            # Prevent infinite logging recursion by ignoring exceptions raised in logging code
            if exc_tb:
                tb = exc_tb
                while tb.tb_next:
                    tb = tb.tb_next
                filename = tb.tb_frame.f_code.co_filename
                if 'db_logger.py' in filename or 'tasks.py' in filename or 'monkeypatch.py' in filename:
                    return
            
            traceback_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            
            # Fetch request from thread-local
            from Home.db_logger import get_current_request
            request = get_current_request()
            
            module = "views"
            actor_id = None
            request_payload = None
            
            if request:
                if request.resolver_match:
                    module = request.resolver_match.app_name or request.resolver_match.view_name or "views"
                else:
                    module = "views"
                
                try:
                    from Home.middleware import DBLoggingMiddleware
                    middleware = DBLoggingMiddleware(None)
                    actor_id, _ = middleware.get_actor_info(request)
                    request_payload = middleware.get_request_payload(request)
                except Exception:
                    pass
            
            # Write to error log table
            from Home.db_logger import log_error
            log_error(
                module=module,
                error_type=exc_type.__name__ if exc_type else "HandledException",
                error_message=str(exc_value),
                traceback_str=traceback_str,
                request_payload=request_payload,
                actor_id=actor_id
            )
    except Exception:
        pass

# Apply the monkeypatch globally
traceback.print_exc = patched_print_exc
print("--- ClassLens traceback.print_exc monkeypatched successfully ---")
