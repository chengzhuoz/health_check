# health_check

用 Django 和 Celery 做的服务健康检查，能管理团队和服务、手动发起巡检、统计每天的健康率。

## 运行

先准备好 Python 和 Redis，在项目目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DJANGO_SECRET_KEY = '改成自己的随机密钥'
python manage.py migrate
python manage.py runserver
```

Redis 默认用 `localhost:6379` 的 0 号库，地址可以通过环境变量 `CELERY_BROKER_URL` 修改。

再开两个终端，进入项目目录，激活虚拟环境，设置和上面一样的 `DJANGO_SECRET_KEY`，分别运行：

```powershell
celery -A health_check worker --pool=solo -l info
```

```powershell
celery -A health_check beat -l info
```

Windows 本地调试用 `solo`，正式部署用 Linux，Celery 官方不支持 Windows。

## 接口

| 地址 | 用途 |
| --- | --- |
| `/api/teams/` | 团队增删改查 |
| `/api/services/` | 服务增删改查 |
| `/api/services/{id}/trigger_check/` | POST 发起巡检 |

新增服务传 `team`、`name`、`health_check_url`、`token`。`environment` 可选 `dev`、`test`、`prod`，不传就是 `dev`。查询不会返回 Token。

每 8 小时换一次本地 Token，每天零点统计昨天的数据，时间按 UTC 算。巡检需要手动调用接口。

Token 目前只是 Base64 编码，换 Token 后还要和被巡检的服务对接。接口没做登录限制，目前用于本地练习。

## 测试

```powershell
python manage.py check
python manage.py test monitor
```
