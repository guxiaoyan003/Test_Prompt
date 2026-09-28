"""Test_Prompt 项目的 ASGI 入口。"""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_prompt.settings')

application = get_asgi_application()
