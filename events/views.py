import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from events.producer import publish_event 


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

class StartVideoUploadView(APIView):

    def post(self, request):
        video_id = str(uuid.uuid4())

        publish_event(
            topic="video.upload",
            event={
                "video_id": video_id,
                "status": "started",
                "progress": 0,
            }
        )

        return Response({
            "video_id": video_id
        })