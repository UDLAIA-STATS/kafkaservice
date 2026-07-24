from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from events.producer import publish_event
from django.core.cache import cache
from events.serializers import (
    StartAnalysisSerializer,
    UploadStatsSerializer,
    VideoUploadSerializer,
)
import traceback

from events.services.player_stats_retrieve_service import handle_stats_details
from events.services.seasons_with_stats_service import handle_stats_by_season
from events.services.stats_retrieve_service import handle_general_stats


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
            traceback.print_exc()
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
                    "color": request.data.get("color"),
                    "analized": request.data.get("analized"),
                },
            )

            return Response(
                {
                    "status": "Los stats están siendo procesados",
                    "stats": request.data.get("stats"),
                    "match_id": request.data.get("match_id"),
                }
            )
        except ValueError as e:
            traceback.print_exc()
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
                },
            )

            return Response(
                {
                    "video_id": video_id,
                    "status": status,
                    "progress": progres,
                }
            )
        except ValueError as e:
            traceback.print_exc()
            return Response({"error": str(e)}, status=400)


class StartAnalysisView(APIView):
    def post(self, request):
        try:
            serializer = StartAnalysisSerializer(data=request.data)

            if not serializer.is_valid():
                raise ValueError(serializer.errors)
            id_partido = request.data.get("match_id")
            color = request.data.get("color")
            video_id = request.data.get("video_name")
            nickname = request.data.get("nickname")

            publish_event(
                topic="start.analysis",
                event={
                    "match_id": id_partido,
                    "color": color,
                    "video_name": video_id,
                    "nickname": nickname,
                },
            )

            return Response(
                {
                    "id_partido": id_partido,
                    "color": color,
                    "video_id": video_id,
                }
            )
        except ValueError as e:
            traceback.print_exc()
            return Response({"error": str(e)}, status=400)

class GeneralStatsView(APIView):
    def get(self, request):
            try:    
                return Response(data=handle_general_stats({}))
            except ValueError as e:
                traceback.print_exc()
                return Response({"error": str(e)}, status=400)

class GetStatsDataView(APIView):
    def get(self, request, temporada_id, torneo_id):

        if not temporada_id:
            return Response({"error": "temporada_id es requerido"}, status=400)

        try:
            result = cache.get(f"stats-{temporada_id}-{torneo_id}")

            if not result:
                result =  handle_stats_details(temporada_id, torneo_id)
                cache.set(f"stats-{temporada_id}-{torneo_id}", result, 150)

            return Response(data=result)
        except ValueError as e:
            traceback.print_exc()
            return Response({"error": str(e)}, status=400)

class GetStatsBySeason(APIView):
    def get(self, request):
        try:
            seasons = handle_stats_by_season()
            return Response(data=seasons)
        except ValueError as e:
            traceback.print_exc()
            return Response({"error": str(e)}, status=400)