from rest_framework import serializers

class VideoUploadSerializer(serializers.Serializer):
    video_id = serializers.CharField()
    progress = serializers.IntegerField()
    status = serializers.ChoiceField(choices=["uploading", "started", "finished"])

    def validate_video_id(self, obj):
        if not obj:
            raise serializers.ValidationError("video_id es requerido")
        if not isinstance(obj, str):
            raise serializers.ValidationError("video_id debe ser una cadena")
        if obj.strip() == "":
            raise serializers.ValidationError("video_id no puede estar vacío")
        return obj
    
    def validate_progress(self, obj):
        if not isinstance(obj, int):
            raise serializers.ValidationError("progress debe ser un entero")
        if obj < 0 or obj > 100:
            raise serializers.ValidationError("progress debe estar entre 0 y 100")
        return obj
    
    def validate_status(self, obj):
        valid_statuses = ["uploading", "started", "finished"]
        if obj not in valid_statuses:
            raise serializers.ValidationError(f"status debe ser uno de {valid_statuses}")
        return obj
    
class UploadStatsSerializer(serializers.Serializer):
    stats = serializers.ListField(child=serializers.DictField())
    match_id = serializers.IntegerField()

    def validate_stats(self, obj):
        if not obj:
            raise serializers.ValidationError("stats es requerido")
        if not isinstance(obj, list):
            raise serializers.ValidationError("stats debe ser una lista")
        if not all(isinstance(item, dict) for item in obj):
            raise serializers.ValidationError("cada elemento de stats debe ser un diccionario")
        return obj

    def validate_match_id(self, obj):
        if not obj:
            raise serializers.ValidationError("match_id es requerido")
        if not isinstance(obj, int):
            raise serializers.ValidationError("match_id debe ser un entero")
        if obj <= 0:
            raise serializers.ValidationError("match_id debe ser un entero positivo")
        return obj
