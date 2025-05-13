from django.contrib import admin
from django.utils.html import format_html
from .models import VideoAllProxy, VideoPublishedProxy


@admin.register(VideoAllProxy)
class VideoAllAdmin(admin.ModelAdmin):
    """Admin interface for VideoAllProxy model with enhanced features."""
    list_display = [
        'title', 
        'display_id', 
        'state', 
        'video_id', 
        'display_published_status',
        'get_playlist_ids',
        'created_at'
    ]
    search_fields = ['title', 'video_id', 'get_playlist_ids']
    list_filter = ['state', 'active', 'created_at']
    readonly_fields = [
        'id', 
        'is_published', 
        'publish_timestamp', 
        'get_playlist_ids',
        'created_at',
        'updated_at'
    ]
    list_per_page = 25
    date_hierarchy = 'publish_timestamp'
    ordering = ['-created_at']
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'state')
        }),
        ('Metadata', {
            'fields': ('id', 'video_id', 'get_playlist_ids'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'publish_timestamp'),
            'classes': ('collapse',)
        }),
    )

    def display_id(self, obj):
        """Formatted display for ID field."""
        return f"VID-{obj.id:08d}"
    display_id.short_description = 'ID'

    def display_published_status(self, obj):
        """Color-coded published status."""
        if obj.is_published:
            return format_html(
                '<span style="color: green; font-weight: bold;">Published</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">Draft</span>'
        )
    display_published_status.short_description = 'Status'


@admin.register(VideoPublishedProxy)
class VideoPublishedProxyAdmin(admin.ModelAdmin):
    """Admin interface for published videos only."""
    list_display = [
        'title', 
        'video_id', 
        'publish_timestamp',
        'playlist_links'
    ]
    search_fields = ['title', 'video_id', 'get_playlist_ids']
    list_per_page = 20
    date_hierarchy = 'publish_timestamp'
    ordering = ['-publish_timestamp']
    actions = ['unpublish_selected']

    def get_queryset(self, request):
        """Return only active published videos."""
        return super().get_queryset(request).filter(active=True)

    def playlist_links(self, obj):
        """Display playlist IDs as clickable links."""
        playlist_ids = obj.get_playlist_ids()
        if not playlist_ids:
            return "-"
        
        links = []
        for pid in playlist_ids.split(','):
            links.append(f'<a href="/admin/playlists/playlist/{pid}/">{pid}</a>')
        return format_html(', '.join(links))
    playlist_links.short_description = 'Playlists'
    playlist_links.allow_tags = True

    def unpublish_selected(self, request, queryset):
        """Custom action to unpublish selected videos."""
        updated = queryset.update(active=False)
        self.message_user(
            request,
            f'{updated} video(s) were successfully unpublished.',
            messages.SUCCESS
        )
    unpublish_selected.short_description = 'Unpublish selected videos'
