from rest_framework import serializers
from signup.models import Concert, Performance, User

class ConcertSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only = True)
    # Send id of manager
    manager = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    location = serializers.CharField()
    dateandtime = serializers.DateTimeField()
    maxtime = serializers.IntegerField()
    piano = serializers.BooleanField()
    locked = serializers.BooleanField()
    description = serializers.CharField()
    signuplink = serializers.URLField()
    title = serializers.CharField()

    def create(self, validated_data):
        return Concert.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.location = validated_data.get('location', instance.location)
        instance.dateandtime = validated_data.get('dateandtime', instance.dateandtime)
        instance.maxtime = validated_data.get('maxtime', instance.maxtime)
        instance.piano = validated_data.get('piano', instance.piano)
        instance.locked = validated_data.get('locked', instance.locked)
        instance.description = validated_data.get('description', instance.description)
        instance.signuplink = validated_data.get('signuplink', instance.signuplink)
        instance.title = validated_data.get('title', instance.title)
        instance.save()
        return instance


class PerformanceSerializer(serializers.ModelSerializer):
    performer = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    class Meta:
        model = Performance
        fields = ['id', 'performer', 'concert', 'piece', 'composer', 'arranger', 'duration', 'comment']
