# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-05-02 14:24
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0012_auto_20180502_1253'),
    ]

    operations = [
        migrations.RenameField(
            model_name='container',
            old_name='prev_predicted_rr',
            new_name='b',
        ),
        migrations.RenameField(
            model_name='container',
            old_name='prev_real_rr',
            new_name='s',
        ),
    ]
