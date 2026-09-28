"""基础信息模块：模型服务（供应商）表 ai_server、模型（含计费标准）表 ai_model。"""
from decimal import Decimal

from django.db import models

# 原型中的「聚合平台」：平台 / 官方名以此开头的条目会带上聚合平台标记
AGGREGATORS = ('硅基流动', 'OpenRouter', '魔搭社区')
# 原型中的「区域部署」：区域化端点部署的平台，模型列表中原型会带上区域部署标记
REGIONAL_PLATFORMS = ('Azure OpenAI',)


def amount_text(value):
    """按原样输出金额：只去掉尾部多余的 0，不做四舍五入，也不用科学计数法。"""
    text = format(value, 'f')
    if '.' in text:
        text = text.rstrip('0').rstrip('.')
    return text or '0'


class AiServer(models.Model):
    """模型服务（供应商）表 ai_server。"""

    plat_name = models.CharField('平台/官方名称', max_length=100)
    base_url = models.CharField('API 基础地址(base_url)', max_length=255)
    comp_name = models.CharField('公司名称', max_length=100, null=True, blank=True)
    home_url = models.CharField('官网首页地址', max_length=255, null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'ai_server'
        verbose_name = '模型服务（供应商）'
        verbose_name_plural = '模型服务（供应商）'
        constraints = [
            models.UniqueConstraint(fields=['plat_name'], name='uk_plat_name'),
        ]

    def __str__(self):
        return self.plat_name

    @property
    def is_aggregator(self):
        """平台 / 官方名以聚合平台名开头时，原型会在列表与下拉框中带上标记。"""
        return self.plat_name.startswith(AGGREGATORS)

    @property
    def is_regional(self):
        """区域化端点部署的平台（Azure 等），原型在模型行上带「区域部署」标记。"""
        return self.plat_name in REGIONAL_PLATFORMS


class AiModel(models.Model):
    """模型（含计费标准）表 ai_model。"""

    srv = models.ForeignKey(
        AiServer,
        on_delete=models.RESTRICT,
        db_column='srv_id',
        related_name='ai_models',
        verbose_name='服务ID',
    )
    model_name = models.CharField('模型名称', max_length=100)
    in_price = models.DecimalField(
        '输入token计费单价', max_digits=12, decimal_places=6, default=Decimal('0.000000')
    )
    out_price = models.DecimalField(
        '输出token计费单价', max_digits=12, decimal_places=6, default=Decimal('0.000000')
    )
    bill_unit = models.CharField('计费单位', max_length=30, default='per_1m_token')
    model_type = models.CharField('模型类型', max_length=30, null=True, blank=True)
    doc_url = models.CharField('模型说明/文档网址', max_length=255, null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'ai_model'
        verbose_name = '模型（含计费标准）'
        verbose_name_plural = '模型（含计费标准）'

    def __str__(self):
        return self.model_name

    @property
    def type_list(self):
        """模型类型：添加页可多选，落库时以「,」拼接，列表页拆分为标签展示。"""
        raw = (self.model_type or '').replace('，', ',')
        return [item.strip() for item in raw.split(',') if item.strip()]

    @property
    def is_free(self):
        """输入 / 输出计费均为 0：原型在模型行上标记「免费 / 限免」。"""
        return self.in_price == 0 and self.out_price == 0

    @property
    def in_price_na(self):
        """输入计费为 0 且不属于全免模型：该维度不计费，原型显示「—」。"""
        return self.in_price == 0 and not self.is_free

    @property
    def out_price_na(self):
        """输出计费为 0 且不属于全免模型：该维度不计费，原型显示「—」。"""
        return self.out_price == 0 and not self.is_free

    @property
    def in_price_text(self):
        """输入计费文案：单价 + 计费单位，如 17.5/K（原样显示，不做四舍五入）。"""
        return self._price_text(self.in_price)

    @property
    def out_price_text(self):
        """输出计费文案：单价 + 计费单位，如 70/K（原样显示，不做四舍五入）。"""
        return self._price_text(self.out_price)

    @property
    def in_price_raw(self):
        """输入计费原值（不带计费单位），供列表页 data-* 与区间过滤使用。"""
        return amount_text(self.in_price)

    @property
    def out_price_raw(self):
        """输出计费原值（不带计费单位），供列表页 data-* 与区间过滤使用。"""
        return amount_text(self.out_price)

    def _price_text(self, value):
        text = amount_text(value)
        return '%s/%s' % (text, self.bill_unit) if self.bill_unit else text
