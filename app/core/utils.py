import socket
from fastapi import Request


def get_client_ip(request: Request) -> str:
    """Extract real client IP address from request headers or client host."""
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    x_real_ip = request.headers.get("x-real-ip")
    if x_real_ip:
        return x_real_ip.strip()
    if request.client:
        return request.client.host
    return "127.0.0.1"


def get_machine_ip() -> str:
    """Get the local machine's primary IP address."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


__all__ = ["get_client_ip", "get_machine_ip"]
