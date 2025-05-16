from django.urls import include, path
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import *
from .views import UserViewSet, PlantViewSet, ScheduleViewSet, PlantBoundaryViewSet, DataCollectorViewSet, user_login, change_pwd, current_time, get_user_schedules, get_approver_schedule, get_schedule_approver_by_id, post_user_schedules, InsertScheduleViewSet, ApproverMenuViewSet, CollectorMenuViewSet, SuperAdminMenuViewSet


router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'plants', PlantViewSet)
router.register(r'pboundaries', PlantBoundaryViewSet)
router.register(r'schedules', ScheduleViewSet)
router.register(r'insertschedules', InsertScheduleViewSet, basename='insertSchedule')
router.register(r'collectedata', DataCollectorViewSet)
router.register(r'approverlist', ApproverMenuViewSet, basename="approverlist")
router.register(r'collectorslist', CollectorMenuViewSet, basename="collectorslist")
router.register(r'superadminlist', SuperAdminMenuViewSet, basename="superadminlist")


urlpatterns = [
    path('login/', user_login, name='user_login'),
    path('changepwd/', change_pwd, name='change_pwd'),
    path('userschedules/', get_user_schedules, name='get_user_schedules'),
    path('apprschedules/', get_approver_schedule, name='get_approver_schedule'),
    path('apprschedulesid/', get_schedule_approver_by_id, name='get_schedule_approver_by_id'),
    path('collschedulesid/', get_schedule_collector_by_id, name='get_schedule_collector_by_id'),
    path('entireschedule', get_schedule_entire_data, name='get_schedule_entire_data'),
    path('export_schedule', export_schedule_csv, name="export_schedule"),
    path('checkdc/', post_user_schedules, name='post_user_schedules'),
    path('predictschedule/', schedule_prediction, name='schedule_prediction'),
    path('gcd/', get_collected_data, name='get_collected_data'),
    path('currenttime/', current_time, name='current_time'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),

]
