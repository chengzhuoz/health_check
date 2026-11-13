from kombu.exceptions import OperationalError
from redis.exceptions import RedisError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Team, Service
from .serializers import TeamSerializer, ServiceSerializer
from .tasks import trigger_health_check


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

    @action(detail=True, methods=['post'])
    def trigger_check(self, request, pk=None):
        service = self.get_object()
        try:
            task = trigger_health_check.apply_async(args=[service.id], retry=False)
        except (OperationalError, RedisError):
            return Response(
                {'detail': '任务队列不可用，请检查 Redis 连接。'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({
            'message': '巡检任务已提交',
            'task_id': task.id,
        }, status=status.HTTP_202_ACCEPTED)
