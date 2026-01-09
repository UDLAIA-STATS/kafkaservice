from django.urls import path, re_path

from events.consumer import VideoProgressConsumer
from events.views import KafkaEventView, StartVideoUploadView, StartVideoAnalysisView

websocket_urlpatterns = [
    re_path(
        r"ws/video-progress/(?P<video_id>[^/]+)/$",
        VideoProgressConsumer.as_asgi()), #type: ignore
]

urlpatterns = [
    path("post_event/", KafkaEventView.as_view()),
    path("start-video-analysis/", StartVideoAnalysisView.as_view()),
    path("start-video-upload/", StartVideoUploadView.as_view()),
]
