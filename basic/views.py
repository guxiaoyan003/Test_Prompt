"""基础信息：服务器列表 / 添加服务器（list_server.html、server_add.html）、
模型列表 / 添加模型（model_list.html、model_add.html）、
提示词调试（prompt_dis.html，真实调用所选模型）。

按原型约定：必填等校验只在原型自带的前端完成，服务端不再重复校验；
服务端只负责落库，并处理数据库层面的错误（平台名唯一约束、外键 RESTRICT）。
"""
import json
import urllib.error
import urllib.request
from decimal import Decimal, InvalidOperation

from django.db import IntegrityError
from django.db.models import Prefetch, RestrictedError
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .models import AiModel, AiServer

# 调试时调用远端接口的超时时间（秒）
PROMPT_TIMEOUT = 180


def _json_body(request):
    try:
        return json.loads(request.body or '{}')
    except (TypeError, ValueError):
        return {}


def _amount(value):
    """计费金额：原型已保证只输入数字与小数点，这里直接转换（留空按 0 计）。"""
    text = (value or '').strip()
    return Decimal(text) if text else Decimal('0')


def _by_id(model, value):
    """按 id 取一条记录：id 非法或记录不存在都返回 None。"""
    text = str(value)
    return model.objects.filter(id=int(text)).first() if text.isdigit() else None


def _api_error(exc):
    """从远端错误体里尽量取出 error.message，取不到就退回接口返回的原始内容。"""
    try:
        detail = json.loads(exc.read().decode('utf-8', 'replace'))
    except (ValueError, OSError):
        return str(exc.reason or exc)
    if isinstance(detail, dict):
        error = detail.get('error')
        if isinstance(error, dict) and error.get('message'):
            return error['message']
        if isinstance(error, str) and error:
            return error
        if detail.get('message'):
            return detail['message']
    return json.dumps(detail, ensure_ascii=False)


def _platform_options():
    """下拉框内置选项：已登记的平台 / 官方名，顺序与列表页一致。"""
    return [
        {'name': srv.plat_name, 'agg': srv.is_aggregator}
        for srv in AiServer.objects.order_by('id')
    ]


@ensure_csrf_cookie
def server_list(request):
    """服务器列表：平台 / 官方名、公司名支持服务端检索。"""
    platform = (request.GET.get('platform') or '').strip()
    company = (request.GET.get('company') or '').strip()

    servers = AiServer.objects.order_by('id')
    if platform:
        servers = servers.filter(plat_name__icontains=platform)
    if company:
        servers = servers.filter(comp_name__icontains=company)

    return render(request, 'basic/list_server.html', {
        'active_nav': 'server_list',
        'servers': servers,
        'f_platform': platform,
        'f_company': company,
    })


@ensure_csrf_cookie
def server_add(request):
    """添加服务器：GET 渲染原型表单，POST（JSON）落库后由前端提示并跳回列表。"""
    if request.method == 'POST':
        data = _json_body(request)
        plat_name = (data.get('plat_name') or '').strip()
        try:
            server = AiServer.objects.create(
                plat_name=plat_name,
                base_url=(data.get('base_url') or '').strip(),
                comp_name=(data.get('comp_name') or '').strip() or None,
                home_url=(data.get('home_url') or '').strip() or None,
            )
        except IntegrityError:
            return JsonResponse({'ok': False, 'error': '平台 / 官方名「%s」已存在' % plat_name})
        return JsonResponse({'ok': True, 'id': server.id, 'plat_name': server.plat_name})

    return render(request, 'basic/server_add.html', {
        'active_nav': 'server_add',
        'platform_options': _platform_options(),
    })


@require_POST
def server_delete(request):
    """删除服务器：原型为表格内删除，这里从 ai_server 表真正删除。"""
    ids = _json_body(request).get('ids') or []
    ids = [int(i) for i in ids if str(i).isdigit()]
    if not ids:
        return JsonResponse({'ok': False, 'error': '请先选择要删除的服务器'})

    try:
        deleted, _ = AiServer.objects.filter(id__in=ids).delete()
    except (RestrictedError, IntegrityError):
        return JsonResponse({'ok': False, 'error': '该服务器下已关联模型，无法删除'})
    return JsonResponse({'ok': True, 'deleted': deleted})


@require_POST
def server_update(request):
    """编辑服务器：按 id 更新 ai_server，字段与「添加服务器」一致。"""
    data = _json_body(request)
    server = _by_id(AiServer, data.get('id'))
    if server is None:
        return JsonResponse({'ok': False, 'error': '要编辑的服务器不存在，请刷新后重试'})

    plat_name = (data.get('plat_name') or '').strip()
    server.plat_name = plat_name
    server.base_url = (data.get('base_url') or '').strip()
    server.comp_name = (data.get('comp_name') or '').strip() or None
    server.home_url = (data.get('home_url') or '').strip() or None
    try:
        server.save()
    except IntegrityError:
        return JsonResponse({'ok': False, 'error': '平台 / 官方名「%s」已存在' % plat_name})
    return JsonResponse({'ok': True, 'id': server.id, 'plat_name': server.plat_name})


@ensure_csrf_cookie
def model_list(request):
    """模型列表：原型上的筛选 / 全选 / 删除都在页面上完成，行数据来自 ai_model 表。"""
    return render(request, 'basic/model_list.html', {
        'active_nav': 'model_list',
        'models': AiModel.objects.select_related('srv').order_by('id'),
        'servers': AiServer.objects.order_by('id'),
    })


@ensure_csrf_cookie
def model_add(request):
    """添加模型：GET 渲染原型表单，POST（JSON）落库后由前端提示并跳回列表。"""
    if request.method == 'POST':
        data = _json_body(request)
        plat_name = (data.get('srv_name') or '').strip()
        model_name = (data.get('model_name') or '').strip()

        server = AiServer.objects.filter(plat_name=plat_name).first()
        if server is None:
            return JsonResponse({'ok': False, 'error': '服务器「%s」未登记，请先添加服务器' % plat_name})

        try:
            model = AiModel.objects.create(
                srv=server,
                model_name=model_name,
                in_price=_amount(data.get('in_price')),
                out_price=_amount(data.get('out_price')),
                bill_unit=(data.get('bill_unit') or '').strip(),
                model_type=(data.get('model_type') or '').strip() or None,
                doc_url=(data.get('doc_url') or '').strip() or None,
            )
        except (InvalidOperation, IntegrityError):
            return JsonResponse({'ok': False, 'error': '模型「%s」保存失败，请检查填写内容' % model_name})
        return JsonResponse({'ok': True, 'id': model.id, 'model_name': model.model_name})

    return render(request, 'basic/model_add.html', {
        'active_nav': 'model_add',
        'servers': AiServer.objects.order_by('id'),
    })


@require_POST
def model_delete(request):
    """删除模型：原型为表格内删除，这里从 ai_model 表真正删除。"""
    ids = _json_body(request).get('ids') or []
    ids = [int(i) for i in ids if str(i).isdigit()]
    if not ids:
        return JsonResponse({'ok': False, 'error': '请先选择要删除的模型'})

    deleted, _ = AiModel.objects.filter(id__in=ids).delete()
    return JsonResponse({'ok': True, 'deleted': deleted})


@require_POST
def model_update(request):
    """编辑模型：按 id 更新 ai_model，字段与「添加模型」一致。"""
    data = _json_body(request)
    model = _by_id(AiModel, data.get('id'))
    if model is None:
        return JsonResponse({'ok': False, 'error': '要编辑的模型不存在，请刷新后重试'})

    plat_name = (data.get('srv_name') or '').strip()
    model_name = (data.get('model_name') or '').strip()

    server = AiServer.objects.filter(plat_name=plat_name).first()
    if server is None:
        return JsonResponse({'ok': False, 'error': '服务器「%s」未登记，请先添加服务器' % plat_name})

    try:
        model.srv = server
        model.model_name = model_name
        model.in_price = _amount(data.get('in_price'))
        model.out_price = _amount(data.get('out_price'))
        model.bill_unit = (data.get('bill_unit') or '').strip()
        model.model_type = (data.get('model_type') or '').strip() or None
        model.doc_url = (data.get('doc_url') or '').strip() or None
        model.save()
    except (InvalidOperation, IntegrityError):
        return JsonResponse({'ok': False, 'error': '模型「%s」保存失败，请检查填写内容' % model_name})
    return JsonResponse({'ok': True, 'id': model.id, 'model_name': model.model_name})


@ensure_csrf_cookie
def prompt_dis(request):
    """提示词调试：服务器 / 模型下拉与 Base_url 取自「基础信息」，顺序与列表页一致。"""
    servers = AiServer.objects.order_by('id').prefetch_related(
        Prefetch('ai_models', queryset=AiModel.objects.order_by('id')),
    )
    return render(request, 'basic/prompt_dis.html', {
        'active_nav': 'prompt_dis',
        'servers': servers,
    })


@require_POST
def prompt_run(request):
    """调试一次：按原型给出的服务器 / 模型 / api_key 调一次 chat/completions，返回该次输出。"""
    data = _json_body(request)
    plat_name = (data.get('srv_name') or '').strip()
    server = AiServer.objects.filter(plat_name=plat_name).first()
    if server is None:
        return JsonResponse({'ok': False, 'error': '服务器「%s」未登记，请先在服务器列表中添加' % plat_name})

    payload = json.dumps({
        'model': (data.get('model_name') or '').strip(),
        'messages': data.get('messages') or [],
    }).encode('utf-8')
    call = urllib.request.Request(
        server.base_url.rstrip('/') + '/chat/completions',
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % (data.get('api_key') or '').strip(),
        },
    )

    try:
        with urllib.request.urlopen(call, timeout=PROMPT_TIMEOUT) as resp:
            result = json.loads(resp.read().decode('utf-8', 'replace'))
    except urllib.error.HTTPError as exc:
        return JsonResponse({'ok': False, 'error': '调用失败（HTTP %s）· %s' % (exc.code, _api_error(exc))})
    except (urllib.error.URLError, OSError) as exc:
        return JsonResponse({'ok': False, 'error': '调用失败 · %s' % (getattr(exc, 'reason', None) or exc)})
    except ValueError:
        return JsonResponse({'ok': False, 'error': '调用失败 · 接口返回的不是合法 JSON'})

    try:
        content = result['choices'][0]['message']['content']
    except (KeyError, IndexError, TypeError):
        return JsonResponse({'ok': False, 'error': '调用失败 · 接口返回里没有 choices[0].message.content'})

    return JsonResponse({'ok': True, 'content': content or '', 'usage': result.get('usage') or {}})
