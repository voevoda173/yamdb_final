import csv
import datetime
import logging
import os
import sys

from django.conf import settings
from django.core.management.base import BaseCommand

from reviews.models import Category, Comment, Genre, Review, Title
from users.models import CustomUser

CSV_DIR = os.path.join(settings.BASE_DIR, 'static', 'data')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    stream=sys.stdout,
)


def read_file(filename):
    filepath = os.path.join(CSV_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = list(csv.reader(f))
    reader.pop(0)
    return reader


def create_object(DBclass, row):
    if DBclass == CustomUser:
        kwargs = {'pk': int(row[0]), 'username': row[1], 'email': row[2],
                  'role': row[3]}
    elif DBclass == Category:
        kwargs = {'pk': int(row[0]), 'name': row[1], 'slug': row[2]}
    elif DBclass == Genre:
        kwargs = {'pk': int(row[0]), 'name': row[1], 'slug': row[2]}
    elif DBclass == Title:
        kwargs = {'pk': int(row[0]), 'name': row[1], 'year': row[2],
                  'category': Category.objects.get(pk=int(row[3]))}
    elif DBclass == Review:
        kwargs = {'pk': int(row[0]),
                  'title': Title.objects.get(pk=int(row[1])),
                  'text': row[2],
                  'author': (CustomUser.objects.get(pk=int(row[3]))),
                  'score': int(row[4]),
                  'pub_date': (datetime.datetime.
                               strptime(row[5], '%Y-%m-%dT%H:%M:%S.%fZ'))}
    elif DBclass == Comment:
        kwargs = {'pk': int(row[0]),
                  'review': Review.objects.get(pk=int(row[1])),
                  'text': row[2],
                  'author': (CustomUser.objects.get(pk=int(row[3]))),
                  'pub_date': (datetime.datetime.
                               strptime(row[4], '%Y-%m-%dT%H:%M:%S.%fZ'))}
    DBclass.objects.create(**kwargs)


def addGenre(filename):
    reader = read_file(filename)
    for row in reader:
        title = Title.objects.get(pk=int(row[1]))
        genre = Genre.objects.get(pk=int(row[2]))
        genre.title_genre.add(title)


def read_to_DB(filename, DBclass):
    reader = read_file(filename)
    for row in reader:
        create_object(DBclass, row)


class Command(BaseCommand):
    help = 'заполнение базы данных из csv файлов'

    def handle(self, *args, **options):
        read_to_DB('users.csv', CustomUser)
        read_to_DB('category.csv', Category)
        read_to_DB('genre.csv', Genre)
        read_to_DB('titles.csv', Title)
        addGenre('genre_title.csv')
        read_to_DB('review.csv', Review)
        read_to_DB('comments.csv', Comment)
        logging.info('база данных готова')
