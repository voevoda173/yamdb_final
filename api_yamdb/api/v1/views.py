from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from api.v1.filters import TitleFilter
from api.v1.permissions import (IsAdmin, IsAdminOrReadOnly,
                                IsAuthorAdminModeratorOrReadOnly)
from api.v1.serializers import (CategorySerializer, CommentSerializer,
                                CustomUserSerializer, GenreSerializer,
                                JWTTokenSerializer, ReviewSerializer,
                                SignupSerializer, TitleListSerializer,
                                TitleSerializer)
from reviews.models import Category, Genre, Review, Title
from users.models import CustomUser


class CreateListDestroyViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                               mixins.DestroyModelMixin,
                               viewsets.GenericViewSet):
    """Пользовательский класс вьюсета.
    Создает и удаляет объект и возвращет список объектов.
    """


class GetPostPatchDeleteViewSet(viewsets.ModelViewSet):
    http_method_names = ('get', 'post', 'patch', 'delete')


class CategoryViewSet(CreateListDestroyViewSet):
    """Вьюсет для выполнения операций с объектами модели Category."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class GenreViewSet(CreateListDestroyViewSet):
    """Вьюсет для выполнения операций с объектами модели Genre."""
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class TitleViewSet(GetPostPatchDeleteViewSet):
    """Вьюсет для выполнения операций с объектами модели Title."""
    queryset = Title.objects.all().annotate(
        rating=Avg('reviews__score')
    ).order_by('-year')
    permission_classes = (IsAdminOrReadOnly, )
    filter_backends = (DjangoFilterBackend, )
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return TitleListSerializer
        return TitleSerializer


class ReviewViewSet(GetPostPatchDeleteViewSet):
    """Вьюсет для выполнения операций с объектами модели Review."""
    serializer_class = ReviewSerializer
    permission_classes = (IsAuthorAdminModeratorOrReadOnly,)

    def get_queryset(self):
        title_id = self.kwargs.get('title_id')
        title = get_object_or_404(Title, pk=title_id)
        return title.reviews.all()

    def perform_create(self, serializer):
        title_id = self.kwargs.get('title_id')
        serializer.save(author=self.request.user,
                        title=get_object_or_404(Title, pk=title_id))


class CommentViewSet(GetPostPatchDeleteViewSet):
    """Вьюсет для выполнения операций с объектами модели Comment."""
    serializer_class = CommentSerializer
    permission_classes = (IsAuthorAdminModeratorOrReadOnly,)

    def get_queryset(self):
        title_id = self.kwargs.get('title_id')
        review_id = self.kwargs.get('review_id')
        review = get_object_or_404(Review, title=title_id, pk=review_id)
        return review.comments.all()

    def perform_create(self, serializer):
        title_id = self.kwargs.get('title_id')
        review_id = self.kwargs.get('review_id')
        serializer.save(author=self.request.user,
                        review=get_object_or_404(Review, pk=review_id,
                                                 title=title_id))


class CustomUserViewSet(viewsets.ModelViewSet):
    """Вьюсет для выполнения операций с объектами модели CustomUser."""
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    lookup_field = 'username'
    permission_classes = (IsAdmin,)

    @action(
        methods=['get', 'patch'],
        detail=False,
        url_path='me',
        permission_classes=[permissions.IsAuthenticated],
    )
    def users_own_profile(self, request):
        """Метод для работы пользователя с профилем."""
        current_user = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(current_user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            serializer = self.get_serializer(
                current_user,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(role=current_user.role)
            return Response(serializer.data, status=status.HTTP_200_OK)


def send_confirmation_code(user):
    """Функция отправки кода подтверждения."""
    confirmation_code = default_token_generator.make_token(user)
    send_mail(
        subject='Код подтверждения',
        message=f'Ваш код подтверждения, {confirmation_code}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email]
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    """view-функция получения пользователем токена для API."""
    serializer = SignupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    username = serializer.data['username']
    email = serializer.data['email']
    user, _ = CustomUser.objects.get_or_create(
        username=username, email=email
    )
    send_confirmation_code(user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def get_auth_token(request):
    """Функция генерации и отправки токена."""
    serializer = JWTTokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = get_object_or_404(
        CustomUser,
        username=request.data.get('username')
    )
    confirm_code = request.data.get('confirmation_code')
    if not default_token_generator.check_token(
        user, confirm_code
    ):
        err = f'Пароль не совпадает с отправленным на email {confirm_code}'
        return Response(err, status=status.HTTP_400_BAD_REQUEST)
    token = AccessToken.for_user(user)
    return Response({'token': str(token)}, status=status.HTTP_200_OK)
