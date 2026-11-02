import base64

from django.db import models


def encrypt_token(raw_token):
    # 这里只做 Base64 编码，还不是真正的加密
    return base64.b64encode(raw_token.encode()).decode()


def decrypt_token(encrypted_token):
    return base64.b64decode(encrypted_token.encode()).decode()


class EnvironmentChoices(models.TextChoices):
    DEV = 'dev', 'Development'
    TEST = 'test', 'Testing'
    PROD = 'prod', 'Production'


class Team(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='团队名称')
    owner = models.CharField(max_length=100, verbose_name='负责人')

    def __str__(self):
        return self.name


class Service(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=100, verbose_name='服务名称')
    environment = models.CharField(
        max_length=10, choices=EnvironmentChoices.choices, default=EnvironmentChoices.DEV
    )
    health_check_url = models.URLField(max_length=255, verbose_name='健康检查完整URL')
    encrypted_token = models.CharField(max_length=255, verbose_name='加密的调用Token')

    @property
    def token(self):
        return decrypt_token(self.encrypted_token)

    @token.setter
    def token(self, raw_token):
        self.encrypted_token = encrypt_token(raw_token)

    class Meta:
        unique_together = ('name', 'environment')


class HealthCheckLog(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    status_code = models.IntegerField(null=True, blank=True, verbose_name='HTTP状态码')
    is_success = models.BooleanField(default=False, verbose_name='是否成功')
    response_time_ms = models.IntegerField(null=True, blank=True, verbose_name='响应耗时')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)


class DailyStatistics(models.Model):
    date = models.DateField(verbose_name='统计日期')
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    environment = models.CharField(max_length=10, choices=EnvironmentChoices.choices)
    total_checks = models.IntegerField(default=0, verbose_name='总巡检次数')
    success_checks = models.IntegerField(default=0, verbose_name='成功次数')
    health_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='健康率')

    class Meta:
        unique_together = ('date', 'team', 'environment')
