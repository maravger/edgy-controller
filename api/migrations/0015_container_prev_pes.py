# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-05-11 10:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0014_auto_20180503_1438'),
    ]

    operations = [
        migrations.AddField(
            model_name='container',
            name='prev_pes',
            field=models.FloatField(default=0),
        ),
    ]