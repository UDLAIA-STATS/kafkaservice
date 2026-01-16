import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from events.producer import publish_event
from events.serializers import UploadStatsSerializer, VideoUploadSerializer 


class KafkaEventView(APIView):
    def post(self, request):
        topic = request.data.get("topic")
        payload = request.data.get("payload")

        if not topic or not payload:
            return Response(
                {"error": "topic y payload son requeridos"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            publish_event(topic, payload)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

        return Response({"status": "sent"}, status=200)


class UploadStatsView(APIView):

    def post(self, request):
        try:
            serializer = UploadStatsSerializer(data=request.data)

            if not serializer.is_valid():
                raise ValueError(serializer.errors)

            publish_event(
                topic="upload.stats",
                event={
                    "stats": request.data.get("stats"),
                    "match_id": request.data.get("match_id"),
                }
            )

            return Response({
                "status": "Los stats están siendo procesados",
                "stats": request.data.get("stats"),
                "match_id": request.data.get("match_id"),
            })
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

class StartVideoUploadView(APIView):

    def post(self, request):
        try:
            serializer = VideoUploadSerializer(data=request.data)

            if not serializer.is_valid():
                raise ValueError(serializer.errors)
            
            video_id = request.data.get("video_id")
            status = request.data.get("status")
            progres = request.data.get("progress")

            publish_event(
                topic="video.progress",
                event={
                    "video_id": video_id,
                    "status": status,
                    "progress": progres,
                }
            )

            return Response({
                "video_id": video_id,
                "status": status,
                "progress": progres,
            })
        except ValueError as e:
            return Response({"error": str(e)}, status=400)