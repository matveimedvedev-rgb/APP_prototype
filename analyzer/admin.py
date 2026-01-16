from django.contrib import admin
from .models import AnalysisSession


@admin.register(AnalysisSession)
class AnalysisSessionAdmin(admin.ModelAdmin):
    """Admin interface for AnalysisSession model."""
    list_display = ('id', 'created_at', 'website_url', 'features_count', 'ai_pages_count', 'has_findability_report')
    list_filter = ('created_at',)
    search_fields = ('website_url',)
    readonly_fields = ('created_at', 'features_count', 'ai_pages_count', 'has_findability_report')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('created_at', 'website_url')
        }),
        ('Data', {
            'fields': ('features', 'ai_pages', 'findability_report'),
            'classes': ('wide',)
        }),
        ('Statistics', {
            'fields': ('features_count', 'ai_pages_count', 'has_findability_report'),
            'classes': ('collapse',)
        }),
    )
    
    def features_count(self, obj):
        return obj.features_count
    features_count.short_description = 'Features'
    
    def ai_pages_count(self, obj):
        return obj.ai_pages_count
    ai_pages_count.short_description = 'AI Pages'
    
    def has_findability_report(self, obj):
        return 'Yes' if obj.has_findability_report else 'No'
    has_findability_report.short_description = 'Has Report'
    has_findability_report.boolean = True
