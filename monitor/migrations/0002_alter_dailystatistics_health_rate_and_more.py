from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitor', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dailystatistics',
            name='health_rate',
            field=models.DecimalField(decimal_places=2, max_digits=5, verbose_name='健康率'),
        ),
        migrations.AlterField(
            model_name='healthchecklog',
            name='response_time_ms',
            field=models.IntegerField(blank=True, null=True, verbose_name='响应耗时'),
        ),
    ]
