"""按 list_server.html 原型中的初始数据填充 ai_server 表。"""
from django.db import migrations

SERVERS = [
    ('OpenAI', 'OpenAI', 'https://api.openai.com/v1'),
    ('Azure OpenAI', '微软 Microsoft', 'https://{resource}.openai.azure.com/openai/deployments'),
    ('硅基流动 SiliconFlow', '北京硅基流动科技', 'https://api.siliconflow.cn/v1'),
    ('OpenRouter', 'OpenRouter Inc.', 'https://openrouter.ai/api/v1'),
    ('魔搭社区 ModelScope', '阿里巴巴', 'https://api-inference.modelscope.cn/v1'),
    ('DeepSeek 官方', '杭州深度求索', 'https://api.deepseek.com/v1'),
    ('通义千问 官方', '阿里云计算', 'https://dashscope.aliyuncs.com/compatible-mode/v1'),
    ('智谱 AI 开放平台', '北京智谱华章', 'https://open.bigmodel.cn/api/paas/v4'),
    ('月之暗面 Kimi', '月之暗面科技', 'https://api.moonshot.cn/v1'),
    ('百度千帆', '百度', 'https://qianfan.baidubce.com/v2'),
]


def seed(apps, schema_editor):
    ai_server = apps.get_model('basic', 'AiServer')
    for plat_name, comp_name, base_url in SERVERS:
        ai_server.objects.update_or_create(
            plat_name=plat_name,
            defaults={'comp_name': comp_name, 'base_url': base_url},
        )


def unseed(apps, schema_editor):
    ai_server = apps.get_model('basic', 'AiServer')
    ai_server.objects.filter(plat_name__in=[row[0] for row in SERVERS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('basic', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
