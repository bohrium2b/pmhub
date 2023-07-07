from django.shortcuts import render
from django.db.models.query import QuerySet
from django.db.models.manager import BaseManager
from rest_framework import viewsets
from rest_framework import permissions
from .serializations import ConcertSerializer, PerformanceSerializer
from signup.models import Concert, Performance
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from typing import *

# Create your views here.
class ConcertViewSet(viewsets.ModelViewSet):
    queryset: BaseManager[Concert] = Concert.objects.all()
    serializer_class = ConcertSerializer

class PerformanceViewSet(viewsets.ModelViewSet):
    queryset: BaseManager[Performance] = Performance.objects.all()
    serializer_class = PerformanceSerializer


def UserConcerts(request) -> JsonResponse | None:
    print(request.user)
    concert_ids = Performance.objects.filter(performer__in = [request.user]).values('concert')
    print(f"Concert ids: {concert_ids}")
    queryset: BaseManager[Concert] = Concert.objects.filter(id__in=concert_ids)
    print(queryset)
    if request.method == "GET":
        serialized = ConcertSerializer(queryset, many=True)
        print(serialized)
        return JsonResponse(serialized.data, safe=False)