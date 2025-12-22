"""
Security middleware for webhook endpoints.
"""
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings


class WebhookIPWhitelistMiddleware(MiddlewareMixin):
    """
    Middleware to restrict webhook endpoints to whitelisted IPs.
    
    Set WEBHOOK_ALLOWED_IPS in settings (comma-separated IPs or CIDR blocks).
    """
    
    def process_request(self, request):
        if request.path.startswith('/api/payments/webhooks/'):
            allowed_ips = getattr(settings, 'WEBHOOK_ALLOWED_IPS', [])
            
            if allowed_ips:
                client_ip = self.get_client_ip(request)
                
                if not self.is_ip_allowed(client_ip, allowed_ips):
                    return HttpResponseForbidden('IP address not allowed')
        
        return None
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_ip_allowed(self, ip, allowed_ips):
        """Check if IP is in allowed list."""
        import ipaddress
        
        try:
            client_ip = ipaddress.ip_address(ip)
            for allowed in allowed_ips:
                try:
                    if '/' in allowed:
                        # CIDR block
                        network = ipaddress.ip_network(allowed, strict=False)
                        if client_ip in network:
                            return True
                    else:
                        # Single IP
                        if client_ip == ipaddress.ip_address(allowed):
                            return True
                except ValueError:
                    continue
        except ValueError:
            return False
        
        return False

