"""按 model_list.html 原型中的初始数据填充 ai_model 表（服务器按 ai_server.plat_name 关联）。"""
from django.db import migrations

# (平台 / 官方名, 模型名, 类型, 输入计费, 输出计费, 计费单位)
MODELS = [
    ('OpenAI', 'gpt-4o', '多模态', '17.50', '70.00', 'K'),
    ('OpenAI', 'gpt-4o-mini', '多模态', '1.10', '4.40', 'K'),
    ('OpenAI', 'o3-mini', '推理', '8.60', '34.40', '百万'),
    ('OpenAI', 'text-embedding-3-large', '嵌入', '0.94', '0.00', ''),
    ('Azure OpenAI', 'gpt-4o', '多模态', '18.20', '72.80', ''),
    ('硅基流动 SiliconFlow', 'deepseek-ai/DeepSeek-V3', '对话', '2.00', '8.00', '百万'),
    ('硅基流动 SiliconFlow', 'Qwen/Qwen2.5-72B-Instruct', '对话', '4.13', '4.13', 'K'),
    ('硅基流动 SiliconFlow', 'BAAI/bge-m3', '嵌入', '0.35', '0.00', ''),
    ('硅基流动 SiliconFlow', 'Kwai-Kolors/Kolors', '图像生成', '0.00', '14.00', 'k'),
    ('OpenRouter', 'anthropic/claude-3.7-sonnet', '对话', '21.60', '108.00', ''),
    ('OpenRouter', 'google/gemini-2.0-flash-001', '多模态', '0.72', '2.88', ''),
    ('魔搭社区 ModelScope', 'Qwen/Qwen3-32B', '推理', '1.50', '6.00', ''),
    ('魔搭社区 ModelScope', 'deepseek-ai/DeepSeek-R1-Distill-Qwen-7B', '推理', '0.00', '0.00', ''),
    ('DeepSeek 官方', 'deepseek-chat', '对话', '2.00', '8.00', ''),
    ('DeepSeek 官方', 'deepseek-reasoner', '推理', '4.00', '16.00', ''),
    ('通义千问 官方', 'qwen-max', '对话', '20.00', '80.00', ''),
    ('通义千问 官方', 'qwen-plus', '对话', '0.80', '2.00', ''),
    ('通义千问 官方', 'text-embedding-v3', '嵌入', '0.49', '0.00', ''),
    ('通义千问 官方', 'gte-rerank-v2', '重排序', '0.80', '0.00', ''),
    ('智谱 AI 开放平台', 'glm-4-plus', '对话', '50.00', '50.00', ''),
    ('智谱 AI 开放平台', 'glm-4-flash', '对话', '0.00', '0.00', ''),
    ('月之暗面 Kimi', 'moonshot-v1-8k', '文本生成', '12.00', '12.00', ''),
    ('月之暗面 Kimi', 'kimi-latest', '多模态', '12.00', '12.00', ''),
    ('百度千帆', 'ernie-4.0-turbo-8k', '对话', '30.00', '90.00', ''),
    ('百度千帆', 'bce-embedding-base_v1', '嵌入', '0.50', '0.00', ''),
    ('百度千帆', 'bce-reranker-base_v1', '重排序', '0.50', '0.00', ''),
]


def seed(apps, schema_editor):
    ai_server = apps.get_model('basic', 'AiServer')
    ai_model = apps.get_model('basic', 'AiModel')
    servers = {srv.plat_name: srv for srv in ai_server.objects.all()}

    for plat_name, model_name, model_type, in_price, out_price, bill_unit in MODELS:
        server = servers.get(plat_name)
        if server is None:
            continue
        ai_model.objects.update_or_create(
            srv=server,
            model_name=model_name,
            defaults={
                'model_type': model_type,
                'in_price': in_price,
                'out_price': out_price,
                'bill_unit': bill_unit,
            },
        )


def unseed(apps, schema_editor):
    ai_model = apps.get_model('basic', 'AiModel')
    for _plat_name, model_name, _model_type, _in, _out, _unit in MODELS:
        ai_model.objects.filter(model_name=model_name).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('basic', '0002_seed_ai_server'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
