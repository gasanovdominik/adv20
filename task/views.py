from django.contrib.auth import authenticate
from django.db.models import Count, QuerySet
from django.db.models.fields import return_None
from django.db.models.functions import ExtractWeekDay
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, filters
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from task_manager.models import Task, SubTask, Category
from task_manager.permissions.owner_permissions import IsOwnerOrReadOnly
from task_manager.serializers import (TaskCreateSerialize,
                                      TaskDetailSerializer,
                                      TaskStatusCountSerializer,
                                      SubTaskCreateSerializer, SubTaskSerializer, CategoryCreateSerializer,
                                      RegisterUserSerializer)
from task_manager.utils import set_jwt_cookies


class UserSubTasksListGenericView(ListAPIView):
    serializer_class = SubTaskSerializer

    def get_queryset(self):
        return SubTask.objects.filter(
            owner=self.request.user
        )

class SubTaskPagination(PageNumberPagination):
    page_size = 5

    def get_page_size(self, request):
        page_size = request.query_params.get('page_size')
        if page_size and page_size.isdigit():
            return int(page_size)
        return self.page_size


class SubTaskListCreateView(ListCreateAPIView):
    queryset = SubTask.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = SubTaskPagination

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]

    filterset_fields = ['status', 'deadline']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at']

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SubTaskSerializer
        return SubTaskCreateSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


# class SubTaskListCreateAPIView(APIView, PageNumberPagination):
#     page_size = 5
#
#     def get_queryset(self, request: Request):
#
#         queryset: QuerySet[SubTask] = SubTask.objects.all()
#
#         tasks = request.query_params.getlist('task')
#         status = request.query_params.get('status')
#
#         if tasks:
#             queryset = queryset.filter(task__title__in=tasks)
#
#         if status:
#             valid_statuses = [choice[0] for choice in SubTask.STATUS_CHOICES]
#             if status in valid_statuses:
#                 queryset = queryset.filter(status=status)
#             else:
#                 queryset = queryset.none()
#
#         return queryset.order_by("-created_at")
#
#     def get_page_size(self, request):
#         page_size = request.query_params.get('page_size')
#
#         if page_size and page_size.isdigit():
#             return int(page_size)
#
#         return self.page_size
#
#     def get(self, request: Request) -> Response:
#         subtasks: QuerySet[SubTask] = self.get_queryset(request=request)
#         # subtasks: QuerySet[SubTask] = SubTask.objects.all().order_by("-created_at")
#         results = self.paginate_queryset(queryset=subtasks, request=request, view=self)
#         serializer = SubTaskSerializer(results, many=True)
#         # return Response(data=serializer.data, status=status.HTTP_200_OK)
#         return self.get_paginated_response(data=serializer.data)
#
#     def post(self, request: Request) -> Response:
#         serializer = SubTaskCreateSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         else:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SubTaskDetailUpdateDeleteView(RetrieveUpdateDestroyAPIView):
    queryset = SubTask.objects.all()
    lookup_url_kwarg = 'subtask_id'
    permission_classes = [IsOwnerOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SubTaskSerializer
        return SubTaskCreateSerializer


# class SubTaskDetailUpdateDeleteView(APIView):
#     def get(self, request: Request, **kwargs) -> Response:
#         try:
#             subtask = SubTask.objects.get(id=kwargs['subtask_id'])
#         except SubTask.DoesNotExist:
#             return Response(
#                 data={
#                     "message": "Подзадача не найдена!"
#                 },
#                 status=status.HTTP_404_NOT_FOUND
#             )
#         serializer = SubTaskSerializer(subtask)
#
#         return Response(
#             data=serializer.data,
#             status=status.HTTP_200_OK
#         )
#
#     def put(self, request: Request, **kwargs) -> Response:
#         try:
#             subtask = SubTask.objects.get(id=kwargs['subtask_id'])
#         except SubTask.DoesNotExist:
#             return Response(
#                 data={
#                     "message": "Подзадача не найдена!"
#                 },
#                 status=status.HTTP_404_NOT_FOUND
#             )
#
#         serializer = SubTaskCreateSerializer(instance=subtask, data=request.data)
#
#         if serializer.is_valid():
#             serializer.save()
#
#             return Response(
#                 data=serializer.data,
#                 status=status.HTTP_200_OK
#             )
#
#         else:
#             return Response(
#                 data=serializer.errors,
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#     def delete(self, request: Request, **kwargs) -> Response:
#         try:
#             subtask = SubTask.objects.get(id=kwargs['subtask_id'])
#         except SubTask.DoesNotExist:
#             return Response(
#                 data={
#                     "message": "Подзадача не найдена!"
#                 },
#                 status=status.HTTP_404_NOT_FOUND
#             )
#
#         subtask.delete()
#
#         return Response(
#             data={
#                 "message": "Книга была успешно удалена."
#             },
#             status=status.HTTP_202_ACCEPTED
#         )

class UserTasksListGenericView(ListAPIView):
    serializer_class = TaskDetailSerializer

    def get_queryset(self):
        return Task.objects.filter(
            owner=self.request.user
        )

class TaskListCreateView(ListCreateAPIView):
    WEEKDAY_MAP = {
        'воскресенье': 1,
        'sunday': 1,
        'понедельник': 2,
        'monday': 2,
        'вторник': 3,
        'tuesday': 3,
        'среда': 4,
        'wednesday': 4,
        'четверг': 5,
        'thursday': 5,
        'пятница': 6,
        'friday': 6,
        'суббота': 7,
        'saturday': 7,
    }

    permission_classes = [IsAuthenticatedOrReadOnly]

    queryset = Task.objects.all()

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]

    filterset_fields = ['status', 'deadline']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at']

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TaskDetailSerializer
        return TaskCreateSerialize

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()
        day_of_week = self.request.query_params.get("weekday")

        if day_of_week:
            if day_of_week.lower() not in self.WEEKDAY_MAP:
                raise ValidationError("Неверный день недели!")

            weekday_num = self.WEEKDAY_MAP.get(day_of_week.lower())
            queryset = queryset.annotate(weekday=ExtractWeekDay('deadline')).filter(weekday=weekday_num)

        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TaskDetailUpdateDeleteView(RetrieveUpdateDestroyAPIView):
    queryset = Task.objects.all()
    lookup_url_kwarg = 'task_id'
    permission_classes = [IsOwnerOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TaskDetailSerializer
        return TaskCreateSerialize


# class TaskListCreateAPIView(APIView):
#     WEEKDAY_MAP = {
#         'воскресенье': 1,
#         'sunday': 1,
#         'понедельник': 2,
#         'monday': 2,
#         'вторник': 3,
#         'tuesday': 3,
#         'среда': 4,
#         'wednesday': 4,
#         'четверг': 5,
#         'thursday': 5,
#         'пятница': 6,
#         'friday': 6,
#         'суббота': 7,
#         'saturday': 7,
#     }
#
#     def get_queryset(self, request: Request) -> QuerySet[Task]:
#         queryset: QuerySet[Task] = Task.objects.all()
#         day_of_week = request.query_params.get("weekday")
#
#         if day_of_week:
#             if day_of_week not in self.WEEKDAY_MAP:
#                 raise ValidationError("Неверный день недели!")
#
#             weekday_num = self.WEEKDAY_MAP.get(day_of_week.lower())
#             queryset = queryset.annotate(weekday=ExtractWeekDay('deadline')).filter(weekday=weekday_num)
#
#         return queryset
#
#     def get(self, request: Request) -> Response:
#         tasks = self.get_queryset(request=request)
#         serializer = TaskDetailSerializer(tasks, many=True)
#
#         return Response(
#             data=serializer.data,
#             status=status.HTTP_200_OK
#         )
#
#     def post(self, request: Request) -> Response:
#         serializer = TaskCreateSerialize(data=request.data)
#
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         else:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @api_view(['POST'])
# def tasks_create(request: Request) -> Response:
#     serializer = TaskCreateSerialize(data=request.data)
#
#     if serializer.is_valid():
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
#     else:
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#

# @api_view(['GET'])
# def list_of_tasks(request) -> Response:
#     tasks = Task.objects.all()
#     serializer = TaskDetailSerializer(tasks, many=True)
#
#     return Response(
#         data=serializer.data,
#         status=status.HTTP_200_OK
#     )

# @api_view(['GET'])
# def get_task_by_id(request, task_id: int) -> Response:
#     try:
#         task = Task.objects.get(id=task_id)
#     except Task.DoesNotExist:
#         return Response(
#             data={
#                 "message": "TASK NOT FOUND"
#             },
#             status=404
#         )
#
#     serializer = TaskDetailSerializer(task)
#
#     return Response(
#         data=serializer.data,
#         status=200
#     )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def tasks_count(request) -> Response:
    tasks_cn = Task.objects.count()

    return Response(data=f"{tasks_cn=}", status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def tasks_count_by_status(request) -> Response:
    statuses_count_by_task = Task.objects.values("status").annotate(Count("id"))
    serializer = TaskStatusCountSerializer(statuses_count_by_task, many=True)
    return Response(data=serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def tasks_of_overdue(request) -> Response:
    count_of_overdue_task = Task.objects.filter(deadline__lt=timezone.now()).count()

    return Response(data=f"{count_of_overdue_task=}", status=status.HTTP_200_OK)


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategoryCreateSerializer
    permission_classes = [IsAdminUser]

    @action(
        detail=False,
        methods=['get'],
        url_path='statistic',

    )
    def get_task_count_by_category(self, request: Request) -> Response:
        category_statistic = Category.objects.annotate(
            count_tasks=Count('task')
        )

        data = [
            {
                "id": c.id,
                "name": c.name,
                "count_tasks": c.count_tasks,
            }
            for c in category_statistic
        ]

        return Response(
            data=data,
            status=status.HTTP_200_OK
        )

# ===================================================================================================
# ===================================================================================================
# ===================================================================================================

# User JWT Logic




class LogInAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(
            request=request,
            username=username,
            password=password
        )

        if user:
            response = Response(
                status=status.HTTP_200_OK
            )

            set_jwt_cookies(response=response, user=user)

            return response

        else:
            return Response(
                data={"message": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED
            )


class LogOutAPIView(APIView):
    def post(self, request):
        response = Response(status=status.HTTP_200_OK)

        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')

        return response


class RegisterUserAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = RegisterUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        response = Response(
            data=serializer.data,
            status=status.HTTP_201_CREATED
        )

        set_jwt_cookies(response, user)

        return response