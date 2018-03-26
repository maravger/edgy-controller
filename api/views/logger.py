# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

from rest_framework.decorators import api_view
from rest_framework.decorators import parser_classes
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework import status
import os


# This API expects "start_time", "end_time" and "rt" data, incoming
# from the client side with this exact order.


@api_view(['POST'])
@parser_classes((JSONParser,))
def collect(request, format=None):
    try:
        os.mkdir('logs')
    except Exception:
        pass

    if 'start_time' in request.data:
        with open("logs/submitted.log", "a") as temp:
            temp.write(request.data['start_time'] + '\n')
    elif 'end_time' in request.data:
        with open("logs/finished.log", "a") as temp:
            temp.write(request.data['end_time'] + '\n')
    elif 'rt' in request.data:
        with open("logs/rt.log", "a") as temp:
            temp.write(request.data['rt'] + '\n')
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    return Response(status=status.HTTP_201_CREATED)
