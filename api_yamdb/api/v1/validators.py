from rest_framework import serializers


def validate_username_not_me(value):
    """Валидатор, не допускающий создания пользователя с ником 'me'."""
    if value == 'me':
        raise serializers.ValidationError(
            'Нельзя использовать \'me\' в качестве юзернейма'
        )
