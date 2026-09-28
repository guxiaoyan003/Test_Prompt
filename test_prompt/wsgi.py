"""Test_Prompt 项目的 WSGI 入口。"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_prompt.settings')

application = get_wsgi_application()
