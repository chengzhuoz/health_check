from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

import requests
from django.test import TestCase
from django.utils import timezone
from kombu.exceptions import OperationalError
from rest_framework.test import APITestCase

from .models import DailyStatistics, HealthCheckLog, Service, Team
from .tasks import calculate_daily_health_rate, rotate_all_service_tokens, trigger_health_check


class HealthCheckTests(TestCase):
    def setUp(self):
        team = Team.objects.create(name='平台', owner='张三')
        self.service = Service.objects.create(
            team=team,
            name='订单服务',
            health_check_url='https://example.com/health',
            token='test-token',
        )

    @patch('monitor.tasks.requests.get')
    def test_successful_check(self, get):
        get.return_value.__enter__.return_value.status_code = 204
        self.assertTrue(trigger_health_check(self.service.pk))
        log = HealthCheckLog.objects.get()
        self.assertEqual(log.status_code, 204)
        self.assertTrue(log.is_success)
        self.assertGreaterEqual(log.response_time_ms, 0)
        get.assert_called_once_with(
            self.service.health_check_url,
            headers={
                'Authorization': 'Bearer test-token',
                'User-Agent': 'HealthCheck-Inspector/1.0',
            },
            timeout=5,
        )

    @patch('monitor.tasks.requests.get', side_effect=requests.Timeout)
    def test_timeout_is_logged(self, get):
        self.assertFalse(trigger_health_check(self.service.pk))
        log = HealthCheckLog.objects.get()
        self.assertIsNone(log.status_code)
        self.assertFalse(log.is_success)

    def test_token_rotation(self):
        rotate_all_service_tokens()
        self.service.refresh_from_db()
        self.assertEqual(len(self.service.token), 32)
        self.assertNotEqual(self.service.token, 'test-token')
        self.assertNotEqual(self.service.token, self.service.encrypted_token)

    def test_daily_statistics_can_be_recalculated(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        started_at = timezone.make_aware(datetime.combine(yesterday, datetime.min.time()))
        success = HealthCheckLog.objects.create(service=self.service, is_success=True)
        failure = HealthCheckLog.objects.create(service=self.service, is_success=False)
        HealthCheckLog.objects.filter(pk__in=[success.pk, failure.pk]).update(created_at=started_at)
        HealthCheckLog.objects.create(service=self.service, is_success=True)

        calculate_daily_health_rate()
        stat = DailyStatistics.objects.get()
        self.assertEqual(stat.date, yesterday)
        self.assertEqual(stat.total_checks, 2)
        self.assertEqual(stat.success_checks, 1)
        self.assertEqual(stat.health_rate, Decimal('50.00'))

        HealthCheckLog.objects.filter(pk=failure.pk).update(is_success=True)
        calculate_daily_health_rate()
        stat.refresh_from_db()
        self.assertEqual(DailyStatistics.objects.count(), 1)
        self.assertEqual(stat.success_checks, 2)
        self.assertEqual(stat.health_rate, Decimal('100.00'))


class ServiceApiTests(APITestCase):
    def setUp(self):
        self.team = Team.objects.create(name='测试团队', owner='张三')
        self.service = Service.objects.create(
            team=self.team,
            name='测试服务',
            health_check_url='https://example.com/health',
            token='old-token',
        )

    def test_create_and_update_service(self):
        response = self.client.post('/api/services/', {
            'team': self.team.pk,
            'name': '新服务',
            'health_check_url': 'https://example.com/health',
            'token': 'first-token',
        })
        self.assertEqual(response.status_code, 201)
        self.assertNotIn('token', response.data)
        self.assertNotIn('encrypted_token', response.data)
        service = Service.objects.get(pk=response.data['id'])
        self.assertEqual(service.token, 'first-token')

        response = self.client.patch(
            f'/api/services/{service.pk}/', {'token': 'new-token'}, format='json'
        )
        self.assertEqual(response.status_code, 200)
        service.refresh_from_db()
        self.assertEqual(service.token, 'new-token')

    @patch('monitor.views.trigger_health_check.apply_async')
    def test_submit_check(self, submit):
        submit.return_value.id = 'test-task'
        response = self.client.post(f'/api/services/{self.service.pk}/trigger_check/')
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data['task_id'], 'test-task')
        submit.assert_called_once_with(args=[self.service.pk], retry=False)

    @patch('monitor.views.trigger_health_check.apply_async', side_effect=OperationalError)
    def test_queue_unavailable(self, submit):
        response = self.client.post(f'/api/services/{self.service.pk}/trigger_check/')
        self.assertEqual(response.status_code, 503)

    def test_token_too_long(self):
        response = self.client.patch(
            f'/api/services/{self.service.pk}/', {'token': '中' * 64}, format='json'
        )
        self.assertEqual(response.status_code, 400)
        self.service.refresh_from_db()
        self.assertEqual(self.service.token, 'old-token')

    @patch('monitor.tasks.requests.get')
    def test_check_with_local_queue(self, get):
        get.return_value.__enter__.return_value.status_code = 200
        app = trigger_health_check.app
        old_eager = app.conf.task_always_eager
        old_broker = app.conf.broker_url
        try:
            app.conf.update(task_always_eager=True, broker_url='memory://')
            response = self.client.post(f'/api/services/{self.service.pk}/trigger_check/')
        finally:
            app.conf.update(task_always_eager=old_eager, broker_url=old_broker)
        self.assertEqual(response.status_code, 202)
        self.assertTrue(response.data['task_id'])
        self.assertTrue(HealthCheckLog.objects.get(service=self.service).is_success)
