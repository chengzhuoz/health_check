import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='服务名称')),
                ('environment', models.CharField(choices=[('dev', 'Development'), ('test', 'Testing'), ('prod', 'Production')], default='dev', max_length=10)),
                ('health_check_url', models.URLField(max_length=255, verbose_name='健康检查完整URL')),
                ('encrypted_token', models.CharField(max_length=255, verbose_name='加密的调用Token')),
            ],
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='团队名称')),
                ('owner', models.CharField(max_length=100, verbose_name='负责人')),
            ],
        ),
        migrations.CreateModel(
            name='HealthCheckLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status_code', models.IntegerField(blank=True, null=True, verbose_name='HTTP状态码')),
                ('is_success', models.BooleanField(default=False, verbose_name='是否成功')),
                ('response_time_ms', models.IntegerField(blank=True, null=True, verbose_name='响应耗时(毫秒)')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='monitor.service')),
            ],
        ),
        migrations.AddField(
            model_name='service',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='services', to='monitor.team'),
        ),
        migrations.AlterUniqueTogether(
            name='service',
            unique_together={('name', 'environment')},
        ),
        migrations.CreateModel(
            name='DailyStatistics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='统计日期')),
                ('environment', models.CharField(choices=[('dev', 'Development'), ('test', 'Testing'), ('prod', 'Production')], max_length=10)),
                ('total_checks', models.IntegerField(default=0, verbose_name='总巡检次数')),
                ('success_checks', models.IntegerField(default=0, verbose_name='成功次数')),
                ('health_rate', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='健康率(%)')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='monitor.team')),
            ],
            options={
                'unique_together': {('date', 'team', 'environment')},
            },
        ),
    ]
