from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_year(value):
    """Функции проверки корректности года создания произведения."""
    if value > timezone.now().year:
        raise ValidationError(
            'Указанный год еще не наступил! Проверьте введенные данные!')
