# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-07 23:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webscraper', '0002_auto_20170306_1826'),
    ]

    operations = [
        migrations.AddField(
            model_name='channel',
            name='status',
            field=models.IntegerField(choices=[(0, 'New'), (1, 'Ok'), (2, 'Warning'), (3, 'Error')], default=0),
        ),
        migrations.AddField(
            model_name='entry',
            name='status',
            field=models.IntegerField(choices=[(0, 'New'), (1, 'Ok'), (2, 'Warning'), (3, 'Error')], default=0),
        ),
    ]
