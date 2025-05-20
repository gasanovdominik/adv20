import re

from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers

from books.models import User
from task_manager.models import Task, SubTask, Category


class TaskStatusCountSerializer(serializers.Serializer):
    status = serializers.CharField()
    id__count = serializers.IntegerField()


# Задание 1: Переопределение полей сериализатора
# Создайте SubTaskCreateSerializer, в котором поле created_at будет доступно только для чтения (read_only).
# Шаги для выполнения:
# Определите SubTaskCreateSerializer в файле serializers.py
# Переопределите поле created_at как read_only.


class SubTaskCreateSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(
        read_only=True
    )

    class Meta:
        model = SubTask
        fields = ["title",
                  "description",
                  "task",
                  "status",
                  "owner",
                  "deadline",
                  "created_at"]

    def validate_deadline(self, value: str):
        if value < timezone.now():
            raise serializers.ValidationError(
                f"Дата не может быть меньше {timezone.now()}"
            )
        return value


# Задание 2: Переопределение методов create и update
# Создайте сериализатор для категории CategoryCreateSerializer, переопределив методы create и update для проверки уникальности названия категории. Если категория с таким названием уже существует, возвращайте ошибку валидации.
# Шаги для выполнения:
# Определите CategoryCreateSerializer в файле serializers.py.
# Переопределите метод create для проверки уникальности названия категории.
# Переопределите метод update для аналогичной проверки при обновлении.

class CategoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["name"]

    def validate_name(self, value: str):
        if value:
            unique_name = Category.objects.filter(name__iexact=value).exists()
            if unique_name:
                raise serializers.ValidationError(
                    "Така категория уже существует!"
                )
        return value

    # def create(self, validated_data: dict[str, str | int | float]) -> Category:
    #     return super().create(validated_data)
    #
    # def update(self, instance: Category, validated_data: dict[str, str | int | float]) -> Category:
    #     return super().update(instance, validated_data)


# Задание 3: Использование вложенных сериализаторов
# Создайте сериализатор для TaskDetailSerializer, который включает вложенный сериализатор для полного отображения связанных подзадач (SubTask).
# Сериализатор должен показывать все подзадачи, связанные с данной задачей.
# Шаги для выполнения:
# Определите TaskDetailSerializer в файле serializers.py.
# Вложите SubTaskSerializer внутрь TaskDetailSerializer.

class SubTaskSerializer(serializers.ModelSerializer):
    task = serializers.StringRelatedField()

    class Meta:
        model = SubTask
        fields = "__all__"


class TaskDetailSerializer(serializers.ModelSerializer):
    subtask_set = SubTaskSerializer(many=True)

    class Meta:
        model = Task
        fields = "__all__"


# Задание 4: Валидация данных в сериализаторах
# Создайте TaskCreateSerializer и добавьте валидацию для поля deadline, чтобы дата не могла быть в прошлом. Если дата в прошлом, возвращайте ошибку валидации.
# Шаги для выполнения:
# Определите TaskCreateSerializer в файле serializers.py.
# Переопределите метод validate_deadline для проверки даты.

class TaskCreateSerialize(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "categories",
            "owner",
            "deadline"
        ]

    def validate_deadline(self, value: str):
        if value < timezone.now():
            raise serializers.ValidationError(
                f"Дата не может быть меньше {timezone.now()}"
            )
        return value


class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    re_password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(
        choices=[
            ("ADMIN", "ADMIN"),
            ("MODERATOR", "MODERATOR"),
            ("LIB MEMBER", "LIB MEMBER"),
        ],
        required=False
    )
    is_staff = serializers.BooleanField(required=False)

    class Meta:
        model = User
        fields = [
            'username', 'first_name',
            'last_name', 'password',
            're_password', 'email',
            'role', 'is_staff',
        ]

    def validate(self, attrs):
        first_name = attrs.get('first_name')
        last_name = attrs.get('last_name')

        re_pattern = r'^[a-zA-Z]+$'

        if not re.match(re_pattern, first_name):
            raise serializers.ValidationError(
                {"first_name": "First name must contain only alphabet characters."}
            )

        if not re.match(re_pattern, last_name):
            raise serializers.ValidationError(
                {"last_name": "Last name must contain only alphabet characters."}
            )

        password = attrs.get('password')
        re_password = attrs.pop('re_password', None)

        if not password:
            raise serializers.ValidationError(
                {"password": "This field is Required."}
            )

        if not re_password:
            raise serializers.ValidationError(
                {"re_password": "This field is Required."}
            )

        validate_password(password)

        if password != re_password:
            raise serializers.ValidationError(
                {"re_password": "Password didn't match."}
            )

        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)

        user.save()

        return user