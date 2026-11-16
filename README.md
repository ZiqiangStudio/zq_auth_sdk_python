# zq-auth-sdk-python

自强统一认证 Python SDK。它只依赖 `requests`，可以在 Django、Flask、FastAPI 或普通脚本里使用。

## 依赖

Python 3.12+

## 安装

```shell
pip install zq-auth-sdk
```

## 使用

```python
from zq_auth_sdk import ZqAuthClient

client = ZqAuthClient(
    appid="your-app-key",
    secret="your-app-secret",
    # 测试环境传入 api_base_url="https://api.test.cas.ziqiang.net.cn"
)

union_id = client.app.sso("one-time-code")["union_id"]
user = client.app.user_info(union_id, detail=True)
```

客户端会在需要时自动完成 app 登录和 token 刷新。`storage` 默认用进程内存；多进程服务传入自己的 `SessionStorage` 实现或 `RedisStorage`。
