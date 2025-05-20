from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from task_manager.views import (tasks_count,
                                tasks_count_by_status,
                                tasks_of_overdue,
                                SubTaskListCreateView,
                                SubTaskDetailUpdateDeleteView,
                                TaskListCreateView,
                                TaskDetailUpdateDeleteView,
                                CategoryViewSet, UserTasksListGenericView, UserSubTasksListGenericView, LogInAPIView,
                                LogOutAPIView)

schema_view = get_schema_view(
    openapi.Info(
        title='Task API',
        default_version='v1',
        description='Our Task API with permissions',
        terms_of_service='https://www.google.com/policies/terms/',
        contact=openapi.Contact(name='Anatoli Panas', email='net@net.net'),
        license=openapi.License(name='OUR LICENSE', url='https://example.com')
    ),
    public=False,
    permission_classes=[permissions.IsAdminUser],
)

router = DefaultRouter()

router.register('categories', CategoryViewSet)

urlpatterns = [
    path('tasks/', TaskListCreateView.as_view()),
    path('tasks/<int:task_id>', TaskDetailUpdateDeleteView.as_view()),
    path('tasks-me/', UserTasksListGenericView.as_view()),
    path('tasks/count', tasks_count),
    path('tasks/status_count', tasks_count_by_status),
    path('tasks/tasks_of_overdue', tasks_of_overdue),

    path('subtasks/', SubTaskListCreateView.as_view()),
    path('subtasks/<int:subtask_id>', SubTaskDetailUpdateDeleteView.as_view()),
    path('subtasks-me/', UserSubTasksListGenericView.as_view()),
    path('', include(router.urls)),
    path('auth-login/', LogInAPIView.as_view()),
    path('auth-logout/', LogOutAPIView.as_view()),
    path('auth-login-jwt/', TokenObtainPairView.as_view()),
    path('token_refresh/', TokenRefreshView.as_view()),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0)),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0)),

]