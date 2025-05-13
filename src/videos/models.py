from django.db import models
from django.db.models.signals import pre_save
from django.utils import timezone
from django.utils.text import slugify
from typing import Optional, List, TypeVar, Type
from django.core.exceptions import ValidationError

from djangoflix.db.models import PublishStateOptions
from djangoflix.db.receivers import publish_state_pre_save, slugify_pre_save

# Type variable for queryset chaining
_VideoQS = TypeVar('_VideoQS', bound='VideoQuerySet')

class VideoQuerySet(models.QuerySet):
    """Custom QuerySet for Video model with published content filtering."""
    
    def published(self: _VideoQS) -> _VideoQS:
        """Return only published videos that should be publicly visible."""
        now = timezone.now()
        return self.filter(
            state=PublishStateOptions.PUBLISH,
            publish_timestamp__lte=now,
            active=True
        )

class VideoManager(models.Manager):
    """Custom manager for Video model with published content access."""
    
    def get_queryset(self) -> VideoQuerySet:
        return VideoQuerySet(self.model, using=self._db)

    def published(self) -> VideoQuerySet:
        """Return only published and active videos."""
        return self.get_queryset().published()

class Video(models.Model):
    """Main video content model with publishing workflow."""
    
    title = models.CharField(max_length=220, help_text="Title of the video")
    description = models.TextField(
        blank=True, 
        null=True,
        help_text="Detailed description of the video content"
    )
    slug = models.SlugField(
        blank=True, 
        null=True,
        unique=True,
        help_text="URL-friendly version of the title"
    )
    video_id = models.CharField(
        max_length=220, 
        unique=True,
        help_text="Unique identifier from the video hosting platform"
    )
    active = models.BooleanField(
        default=True,
        help_text="Whether this video should be visible at all"
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Creation timestamp"
    )
    updated = models.DateTimeField(
        auto_now=True,
        verbose_name="Last update timestamp"
    )
    state = models.CharField(
        max_length=2, 
        choices=PublishStateOptions.choices, 
        default=PublishStateOptions.DRAFT,
        help_text="Publication status"
    )
    publish_timestamp = models.DateTimeField(
        auto_now_add=False,
        auto_now=False, 
        blank=True, 
        null=True,
        help_text="Scheduled publication time"
    )

    objects = VideoManager()

    class Meta:
        ordering = ['-publish_timestamp', '-created']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['video_id']),
            models.Index(fields=['state', 'publish_timestamp']),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.video_id})"

    def clean(self) -> None:
        """Validate model before saving."""
        if self.state == PublishStateOptions.PUBLISH and not self.publish_timestamp:
            raise ValidationError(
                "A publish timestamp is required when state is set to PUBLISH"
            )
        super().clean()

    def get_video_id(self) -> Optional[str]:
        """Get the video ID only if the video is published."""
        return self.video_id if self.is_published else None

    @property
    def is_published(self) -> bool:
        """Check if the video should be publicly visible."""
        if not self.active:
            return False
        if self.state != PublishStateOptions.PUBLISH:
            return False
        if not self.publish_timestamp:
            return False
        return self.publish_timestamp <= timezone.now()

    def get_playlist_ids(self) -> List[int]:
        """Get IDs of all playlists featuring this video."""
        return list(self.playlist_featured.all().values_list('id', flat=True))

class VideoAllProxy(Video):
    """Proxy model for accessing all videos in admin."""
    
    class Meta:
        proxy = True
        verbose_name = 'All Video'
        verbose_name_plural = 'All Videos'
        ordering = ['-created']

class VideoPublishedProxy(Video):
    """Proxy model for accessing only published videos in admin."""
    
    class Meta:
        proxy = True
        verbose_name = 'Published Video'
        verbose_name_plural = 'Published Videos'
        ordering = ['-publish_timestamp']

    def get_queryset(self) -> VideoQuerySet:
        """Return only published videos."""
        return super().get_queryset().published()

# Connect signals to all relevant models
models_to_connect = [Video, VideoAllProxy, VideoPublishedProxy]

for model in models_to_connect:
    pre_save.connect(publish_state_pre_save, sender=model)
    pre_save.connect(slugify_pre_save, sender=model)
