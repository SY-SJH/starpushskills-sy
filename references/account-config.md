# 账号配置格式

账号配置只服务于没有可用已登录浏览器时的 Playwright 后备模式。正常使用 skill 发布时，优先使用同事本人已经登录的可见浏览器，以页面上的昵称或头像识别账号；不要把密码发到聊天，也不要导出浏览器 Cookie。

## 原则

- 每个同事单独一份账号配置。
- skill 发布前先读取当前账号。
- 不同平台账号彼此隔离。

## 配置文件

文件名默认是 skill 目录下的 `accounts.json`。它被本地 `.gitignore` 忽略，每个同事在自己的电脑上填写自己的账号。

多人共用时使用 `accounts` 数组：

```json
{
  "accounts": [
    {
      "name": "zhangsan",
      "platforms": {
        "xiaohongshu": {
          "auth_mode": "password",
          "username": "账号",
          "password": "密码",
          "login_url": "平台登录页",
          "publish_url": "平台发布页",
          "storage_state": "./sessions/zhangsan-xiaohongshu.json",
          "selectors": {}
        },
        "xiaoyunque": {
          "auth_mode": "sms-or-douyin",
          "login_url": "小云雀登录页",
          "generate_url": "小云雀视频生成页",
          "storage_state": "./sessions/zhangsan-xiaoyunque.json",
          "selectors": {}
        }
      }
    },
    {
      "name": "lisi",
      "platforms": {}
    }
  ]
}
```

也兼容 `accounts.example.json` 当前展示的单账号格式：顶层直接写 `name` 和 `platforms`。平台名支持中文名和英文标识，例如 `小红书` 与 `xiaohongshu` 等价。

`auth_mode` 使用 `password` 时才会尝试填写用户名和密码；`sms-or-douyin`、`douyin-login`、`manual`、`qr` 等模式必须先人工登录。`selectors` 需要根据当前网页结构填写，示例中的 `example.com` 地址和 selector 不能直接发布。
