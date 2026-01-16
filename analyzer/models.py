from django.db import models
import json


class AnalysisSession(models.Model):
    """Stores analysis session data for a website."""
    created_at = models.DateTimeField(auto_now_add=True)
    website_url = models.URLField(blank=True, null=True)
    features = models.JSONField(default=list, blank=True)
    ai_pages = models.JSONField(default=list, blank=True)
    findability_report = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Session {self.id} - {self.website_url or 'No URL'}"

    @property
    def features_count(self):
        """Return the count of features."""
        return len(self.features) if isinstance(self.features, list) else 0

    @property
    def ai_pages_count(self):
        """Return the count of AI pages."""
        return len(self.ai_pages) if isinstance(self.ai_pages, list) else 0

    @property
    def has_findability_report(self):
        """Check if findability report exists."""
        return bool(self.findability_report and isinstance(self.findability_report, dict))
