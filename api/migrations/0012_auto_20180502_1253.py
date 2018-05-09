# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-05-02 12:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_auto_20180502_1251'),
    ]

    operations = [
        migrations.RenameField(
            model_name='container',
            old_name='next_rr_limit',
            new_name='next_predicted_rr',
        ),
        migrations.AddField(
            model_name='container',
            name='next_real_rr',
            field=models.FloatField(default=0),
        ),
    ]