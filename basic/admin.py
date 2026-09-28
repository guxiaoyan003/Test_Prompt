from django.contrib import admin

from .models import AiModel, AiServer


@admin.register(AiServer)
class AiServerAdmin(admin.ModelAdmin):
    list_display = ('id', 'plat_name', 'comp_name', 'base_url', 'created_at', 'updated_at')
    search_fields = ('plat_name', 'comp_name', 'base_url')
    ordering = ('id',)


@admin.register(AiModel)
class AiModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'srv', 'model_name', 'model_type', 'in_price', 'out_price', 'bill_unit')
    list_filter = ('model_type', 'bill_unit')
    search_fields = ('model_name',)
    ordering = ('id',)
