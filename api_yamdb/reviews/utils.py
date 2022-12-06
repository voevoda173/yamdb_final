from django.db import models


class NameField(models.CharField):
    """Переводит значение поля в нижний регистр."""

    def to_python(self, value):
        return value.lower()
