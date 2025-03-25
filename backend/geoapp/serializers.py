from rest_framework import serializers
from .models import User, Plant, Schedule, PlantBoundary, DataCollector

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'role']
    
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class PlantBoundarySerializer(serializers.ModelSerializer):
    class Meta:
        model = PlantBoundary
        fields ="__all__"

class PlantSerializer(serializers.ModelSerializer):
    boundaries = PlantBoundarySerializer(many = True, read_only = True)

    class Meta:
        model = Plant
        fields = ['id', 'name', 'boundaries']

class ScheduleSerializer(serializers.ModelSerializer):
    approver = UserSerializer()
    collectors = UserSerializer(many = True)
    plant = PlantSerializer()
    
    class Meta: 
        model = Schedule
        fields  = '__all__'
        # depth = 1


class InsertScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = '__all__'

class DataCollectorSerializer(serializers.ModelSerializer):

    class Meta:
        model = DataCollector
        fields = '__all__'
        depth = 1