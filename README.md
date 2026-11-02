# 服务健康检查

Django + Celery 写的服务巡检项目，记录巡检结果，按团队和环境统计每天的健康率。

## 本地运行

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DJANGO_SECRET_KEY = '换成你自己的随机密钥，几个进程保持一致'
python manage.py migrate
python manage.py runserver
```

任务队列使用 Redis，默认地址是 `redis://localhost:6379/0`，可以通过环境变量 `CELERY_BROKER_URL` 修改。
启动 Redis 后，另外开两个终端，激活虚拟环境并设置同一个 `DJANGO_SECRET_KEY`：

```powershell
celery -A health_check worker --pool=solo -l info
celery -A health_check beat -l info
```

Windows 本地调试使用 `solo`，Celery 官方不支持 Windows，部署时使用 Linux。

## 接口

| 地址 | 用途 |
| --- | --- |
| `/api/teams/` | 团队增删改查 |
| `/api/services/` | 服务增删改查 |
| `/api/services/{id}/trigger_check/` | POST 提交单个服务的巡检任务 |

新增服务时传 `team`、`name`、`environment`、`health_check_url`、`token`。环境可选 `dev`、`test`、`prod`，默认 `dev`。Token 只接收写入，不在接口响应中返回。

## 定时任务

每 8 小时轮换数据库中的 Token，每天零点统计昨天的巡检结果。目前时区是 UTC，可以修改 `TIME_ZONE`。巡检通过接口按需触发，没有配置自动巡检周期。

当前 Token 使用 Base64 编码，轮换也只修改本地数据库；对方服务如何接受新 Token 需要另外对接。接口还没有登录权限限制，仅用于本地练习。

## 检查

```powershell
python manage.py check
python manage.py test monitor
```
