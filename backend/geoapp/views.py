import pandas as pd
from django.contrib.auth import get_user_model, authenticate
from django.http import JsonResponse, HttpResponse
from datetime import datetime, timedelta
# from .models import Plant, Schedule, PlantBoundary, DataCollector
from rest_framework import permissions, viewsets
from rest_framework.decorators import api_view, authentication_classes
from elasticsearch import Elasticsearch
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from geoapp.serializers import *
import mindsdb_sdk
from .models import *
# Create your views here.
User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class PlantBoundaryViewSet(viewsets.ModelViewSet):
    queryset = PlantBoundary.objects.all()
    serializer_class = PlantBoundarySerializer

class PlantViewSet(viewsets.ModelViewSet):
    queryset = Plant.objects.all()
    serializer_class = PlantSerializer

class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer

class InsertScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = InsertScheduleSerializer

class DataCollectorViewSet(viewsets.ModelViewSet):
    queryset = DataCollector.objects.all()
    serializer_class = DataCollectorSerializer

class ApproverMenuViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(role = "Approver")
    serializer_class = UserSerializer

class CollectorMenuViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(role = "Data Collector")
    serializer_class = UserSerializer

class SuperAdminMenuViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(role = "SuperAdmin")
    serializer_class = UserSerializer

@api_view(['POST'])
def change_pwd(request):

    username = request.data.get("username")
    old_pwd = request.data.get("old_pwd")
    new_pwd = request.data.get("new_pwd")
    
    user = authenticate(username=username, password=old_pwd)

    if user is None:
        return Response({"error": "Invalid Username or Password"})    
    
    user.set_password(new_pwd)
    user.save()

    return Response({"message" : "Password changed successfully"})


@api_view(['POST'])
def user_login(request):
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(username=username, password=password)
    

    if user is not None:
        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Login Successful",
            "username": user.username,
            "role": user.role,
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
        })
    else:
        return Response({"error": "Inavlid Username or Password"})

@api_view(['GET'])
def current_time(request):
    now = datetime.now().strftime("%H:%M:%S")
    return Response({"current_time": now})


@api_view(['GET'])
def get_user_schedules(request):
    user = request.user
    schedules = Schedule.objects.select_related('approver').filter(collectors__in=[user.id])
    sch=[]
    for i in schedules:
        pln=PlantBoundary.objects.filter(plant=i.plant.pk).all()

        sch.append({
            "visit_date": i.visit_date,
            "id": i.pk,
            "plant": dict(id=i.plant.id, name=i.plant.name),
            "boundary": [dict(lat=j.latitude, lng=j.longitude) for j in pln]
        })
        print(sch)
        # sch.append(dict(visit_date=i.visit_date, id=i.pk, plant=i.plant.name, pln=pln.latitude if pln else "No Boundary Found"))
    return Response(sch)


@api_view(['GET'])
def get_schedule_collector_by_id(request):

    collector_id = request.query_params.get("collector_id")
    schedules = Schedule.objects.filter(collectors__id=collector_id).distinct()
    sch = []
    for i in schedules:
        plant_boundaries = PlantBoundary.objects.filter(plant=i.plant.pk)

        sch.append({
            "visit_date": i.visit_date,
            "id": i.pk,
            "collectors": [
                {"id": collector.id, "username": collector.username, "role": "Data Collector"}
                for collector in i.collectors.all()
            ],
            "plant": dict(id=i.plant.id, name=i.plant.name),
            "boundary": [dict(lat=j.latitude, lng=j.longitude) for j in plant_boundaries]
        })
    return Response(sch)


@api_view(['GET'])
def get_collected_data(request):
    data_collected = DataCollector.objects.all()
    dc = []
    for i in data_collected:
        plant_boundaries = PlantBoundary.objects.filter(plant=i.plant.pk)
        dc.append({

            "id": i.pk,
            "visit_date": i.visit_date,
            "Name_client": i.Name_client,
            "Designation_client": i.Designation_client,
            "Email_client": i.Email_client,
            "Contact_client": i.Contact_client,
            "start_time": i.start_time.strftime("%H:%M:%S"),
            "end_time": i.end_time.strftime("%H:%M:%S"),
            "dc_location_lat": i.dc_location_lat,
            "dc_location_long": i.dc_location_long,
            "schedule": {
                "id": i.schedule.id,
                "visit_date": i.schedule.visit_date,
                "approver": i.schedule.approver.id,
                "plant": i.schedule.plant.id,
                "collectors": [
                    {"id": collector.id,}
                    for collector in i.schedule.collectors.all()
                ]
            },
            "plant": {
                "id": i.plant.id,
                "name": i.plant.name
            },
            "boundary": [
                {"latitude": j.latitude, "longitude": j.longitude}
                for j in plant_boundaries
            ]
        })
    return Response(dc)

@api_view(http_method_names=['POST'])
def export_schedule_csv(request):
    schedules = Schedule.objects.select_related('approver', 'plant').prefetch_related('collectors')

    data = []

    for schedule in schedules:
        collector_usernames = ', '.join([collector.username for collector in schedule.collectors.all()])
        data.append({
            "Approver": schedule.approver.username,
            "Plant": schedule.plant.name,
            "Collectors": collector_usernames,
            "Visit_date": schedule.visit_date
        })
    df = pd.DataFrame(data)

    response = HttpResponse(content_type='text/csv')
    df.to_csv(path_or_buf=response, index=False)

    return response

@api_view(['POST'])
def post_user_schedules(request):
    # DataCollector.objects.create(**request)
    plant_id = request.data.get("plant_id")

    data_entry = DataCollector.objects.create(
        plant_id=plant_id,
        schedule = Schedule.objects.get(pk=request.data.get("schedule_id")),
        Name_client=request.data.get("Name_client"),
        Designation_client=request.data.get("Designation_client"),
        Email_client=request.data.get("Email_client"),
        Contact_client=request.data.get("Contact_client"),
        start_time=request.data.get("start_time"),
        end_time=request.data.get("end_time"),
        visit_date=request.data.get("visit_date"),
        dc_location_lat=request.data.get("dc_location_lat", 0),
        dc_location_long=request.data.get("dc_location_long", 0),
    )
    
    sch=Schedule.objects.get(pk=request.data.get("schedule_id"))

    plant_boundaries = PlantBoundary.objects.filter(plant=sch.plant.pk)
    collected_data = DataCollector.objects.filter(schedule=sch)


    schdetails = {
        "id": sch.id,
        "approvers": 
            {"id": sch.approver.id, "username": sch.approver.username, "role": "Approver"},
        "collectors": [
            {"id": collector.id, "username": collector.username, "role": "Data Collector"}
            for collector in sch.collectors.all()
        ],
        "plant": {
            "id":sch.plant.id, "name":sch.plant.name, "boundaries": [{"latitude":j.latitude, "longitude":j.longitude} for j in plant_boundaries]},
        "details": [
            {
                "id":data.pk,
                "name_client": data.Name_client,
                "designation_client": data.Designation_client,
                "email_client": data.Email_client,
                "contact_client": data.Contact_client,
                "start_time": data.start_time.isoformat(),
                "end_time": data.end_time.isoformat(),
                "visit_date": data.visit_date.isoformat()   ,
                "dc_location_lat": data.dc_location_lat,
                "dc_location_long": data.dc_location_long
            } for data in collected_data
        ],
        "visit_date": sch.visit_date.isoformat(),
    }

    client = Elasticsearch(
        "https://10.1.15.162:9200",
        api_key="ZWZzTTlaVUIxOUJUZzR5SDVndWI6b3J3SDlpTjhScHFRRGJQZU13NkR2UQ==",
        verify_certs=False
    )

    client.index(
        index="geoapp",
        id=request.data.get("schedule_id"),
        document=schdetails
    )

    return Response({"message": "Saved Well"})

@api_view(['GET'])
def get_approver_schedule(request):
    user = request.user
    schedules = Schedule.objects.filter(approver=user).all()
    sch = []
    for schedule in schedules:
        plant_boundaries = PlantBoundary.objects.filter(plant=schedule.plant.pk)

        sch.append({
            "id": schedule.id,
            "approver": {
                "id": schedule.approver.id,
                "username": schedule.approver.username,
                "role": "Approver"
            },
            "collectors": [
                {"id": collector.id, "username": collector.username, "role": "Data Collector"}
                for collector in schedule.collectors.all()
            ],
            "plant": {
                "id": schedule.plant.id,
                "name": schedule.plant.name,
                "boundaries": [
                    {"id": boundary.id, "latitude": boundary.latitude, "longitude": boundary.longitude}
                    for boundary in plant_boundaries
                ]
            },
            "visit_date": schedule.visit_date
        })
    return Response(sch)

@api_view(['GET'])
def get_schedule_approver_by_id(request):

    approver_id = request.query_params.get("approver_id")
    schedules = Schedule.objects.filter(approver_id=approver_id)
    sch = []
    for schedule in schedules:
        plant_boundaries = PlantBoundary.objects.filter(plant=schedule.plant.pk)

        sch.append({
            "id": schedule.id,
            "approver": {
                "id": schedule.approver.id,
                "username": schedule.approver.username,
                "role": "Approver"
            },
            "collectors": [
                {"id": collector.id, "username": collector.username, "role": "Data Collector"}
                for collector in schedule.collectors.all()
            ],
            "plant": {
                "id": schedule.plant.id,
                "name": schedule.plant.name,
                "boundaries": [
                    {"id": boundary.id, "latitude": boundary.latitude, "longitude": boundary.longitude}
                    for boundary in plant_boundaries
                ]
            },
            "visit_date": schedule.visit_date
        })
    return Response(sch)

@api_view(['GET'])
def schedule_prediction(request):
    server = mindsdb_sdk.connect('http://10.1.15.88:47334')
    current_date = datetime.today()
    dict_data = []
    SchedulePrediction.objects.all().delete()
    for i in range(10):
        query_date = (current_date + timedelta(days=i)).strftime('%Y-%m-%d')
        query = server.databases.geodb.query(
            f"SELECT visit_date, schedule_count as predicted_count FROM mindsdb.schedule_predictor WHERE visit_date = '{query_date}';"
        )
        data=query.fetch().to_dict()
        for j in data['visit_date'].keys():
            model = SchedulePrediction.objects.create(
                visit_date = data["visit_date"][j],
                predicted_schedule_count = data["predicted_count"][j]
            )
            dict_data.append({
                "visit_date": data["visit_date"][j],
                "predicted_schedule_count": data["predicted_count"][j]
            })
    return Response({
        "message": "Predictions saved successfully!",
        "data": dict_data
    })



@api_view(['GET'])
def get_schedule_entire_data(request):

    schedules = Schedule.objects.all()
    sch = []
    for i in schedules:
        plant_boundaries = PlantBoundary.objects.filter(plant=i.plant.pk)
        collected_data = DataCollector.objects.filter(schedule=i)

        sch.append({
            "id": i.pk,
            "approvers": 
                {"id": i.approver.id, "username": i.approver.username, "role": "Approver"},
            "collectors": [
                {"id": collector.id, "username": collector.username, "role": "Data Collector"}
                for collector in i.collectors.all()
            ],
            "plant": {
                "id":i.plant.id, "name":i.plant.name, "boundaries": [{"latitude":j.latitude, "longitude":j.longitude} for j in plant_boundaries]},
            "details": [
                {
                    "id":data.pk,
                    "name_client": data.Name_client,
                    "designation_client": data.Designation_client,
                    "email_client": data.Email_client,
                    "contact_client": data.Contact_client,
                    "start_time": data.start_time,
                    "end_time": data.end_time,
                    "visit_date": data.visit_date,
                    "dc_location_lat": data.dc_location_lat,
                    "dc_location_long": data.dc_location_long
                } for data in collected_data
            ],
            "visit_date": i.visit_date,

        })
    return Response(sch)
