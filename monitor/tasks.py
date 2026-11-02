import secrets
import time
from datetime import datetime, timedelta
from decimal import Decimal

import requests
from celery import shared_task
from django.db.models import Count, Q
from django.utils import timezone

from .models import DailyStatistics, HealthCheckLog, Service


@shared_task
def trigger_health_check(service_id):
    try:
        service = Service.objects.get(pk=service_id)
    except Service.DoesNotExist:
        return 'Service not found'

    headers = {
        'Authorization': f'Bearer {service.token}',
        'User-Agent': 'HealthCheck-Inspector/1.0',
    }
    start_time = time.perf_counter()
    status_code = None
    is_success = False

    try:
        with requests.get(service.health_check_url, headers=headers, timeout=5) as response:
            status_code = response.status_code
            is_success = 200 <= status_code < 300
    except requests.RequestException:
        pass

    HealthCheckLog.objects.create(
        service=service,
        status_code=status_code,
        is_success=is_success,
        response_time_ms=int((time.perf_counter() - start_time) * 1000),
    )
    return is_success


@shared_task
def rotate_all_service_tokens():
    count = 0
    for service in Service.objects.iterator():
        service.token = secrets.token_hex(16)
        service.save(update_fields=['encrypted_token'])
        count += 1
    return f'Rotated tokens for {count} services.'


@shared_task
def calculate_daily_health_rate():
    today = timezone.localdate()
    yesterday = today - timedelta(days=1)
    start_of_yesterday = timezone.make_aware(datetime.combine(yesterday, datetime.min.time()))
    start_of_today = timezone.make_aware(datetime.combine(today, datetime.min.time()))

    stats = HealthCheckLog.objects.filter(
        created_at__gte=start_of_yesterday,
        created_at__lt=start_of_today,
    ).values('service__team_id', 'service__environment').annotate(
        total=Count('id'),
        success=Count('id', filter=Q(is_success=True)),
    )

    daily_stats = []
    for stat in stats:
        health_rate = Decimal(stat['success']) * 100 / stat['total']
        daily_stats.append(DailyStatistics(
            date=yesterday,
            team_id=stat['service__team_id'],
            environment=stat['service__environment'],
            total_checks=stat['total'],
            success_checks=stat['success'],
            health_rate=health_rate.quantize(Decimal('0.01')),
        ))
    if daily_stats:
        # 重跑时更新当天的结果，避免重复插入
        DailyStatistics.objects.bulk_create(
            daily_stats,
            update_conflicts=True,
            update_fields=['total_checks', 'success_checks', 'health_rate'],
            unique_fields=['date', 'team', 'environment'],
        )
    return f'Calculated stats for {len(daily_stats)} dimensions.'
