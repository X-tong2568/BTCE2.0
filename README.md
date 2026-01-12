# B站动态置顶评论与直播监控系统(BTCE)

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![Dependencies](https://img.shields.io/badge/dependencies-playwright%20%7C%20beautifulsoup4-orange)
![Platform](https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macOS-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

> **项目名称说明**：BTCE 是 **B**ilibili **T**op **C**omment forward **E**mail 的缩写，意为"B站置顶评论与直播邮件/QQ通知转发"
> 一个自动监控 B站动态置顶评论及直播状态变化的 Python 程序，当检测到更新时可自动发送邮件与 QQ 推送。

## 功能特点

* 🔍 实时监控 B站动态置顶评论文字和图片
* 📧 自动发送邮件通知（支持完整 HTML+CSS 卡片显示）
* 🐧 可将文本与图片消息推送到 QQ 群（支持 CQ 码发送封面/评论图片）
* 🖼️ 支持监控评论图片和直播封面
* 🎬 直播状态监控（开播/下播/标题变更通知）

## 示例效果

### 1️⃣ 邮件卡片示例（动态置顶评论更新）

<div style="border:1px solid #ddd; padding:10px; max-width:400px; background:#f9f9f9; font-family:Microsoft YaHei">
  <div style="background:linear-gradient(135deg,#2196F3,#1976D2);color:#fff;text-align:center;padding:10px;border-radius:5px">
    <h3>🎉 test_name 动态置顶评论更新</h3>
  </div>
  <div style="padding:10px">
    <p><b>新置顶评论：</b></p>
    <div style="background:#f0f8ff;padding:10px;border-radius:5px">大家好，这是新置顶评论内容</div>
    <p><b>评论图片：</b></p>
    <img src="https://i0.hdslb.com/bfs/article/xxx.jpg" style="max-width:100%; border-radius:5px" />
    <p><b>检测时间：</b>2026-01-12 10:00:00</p>
    <a href="https://t.bilibili.com/123456" style="background:#2196F3;color:#fff;padding:5px 10px;border-radius:3px;text-decoration:none">查看动态</a>
  </div>
  <div style="font-size:12px;color:#999;text-align:center;padding:5px">此邮件由动态监控系统自动发送</div>
</div>

---

### 2️⃣ 邮件卡片示例（直播开播通知）

<div style="border:1px solid #ddd; padding:10px; max-width:400px; background:#f9f9f9; font-family:Microsoft YaHei">
  <div style="background:linear-gradient(135deg,#ff6699,#ff3366);color:#fff;text-align:center;padding:10px;border-radius:5px">
    <h3>🎉 test_name 直播开播提醒</h3>
  </div>
  <div style="padding:10px">
    <p><b>标题：</b>新年特别直播</p>
    <p><b>封面：</b></p>
    <img src="https://i0.hdslb.com/bfs/live/cover.jpg" style="max-width:100%; border-radius:5px" />
    <p><b>监控时间：</b>2026-01-12 10:00:00</p>
    <a href="https://live.bilibili.com/6" style="background:#ff3366;color:#fff;padding:5px 10px;border-radius:3px;text-decoration:none">进入直播间</a>
  </div>
  <div style="font-size:12px;color:#999;text-align:center;padding:5px">此邮件由直播监控系统自动发送</div>
</div>

---

### 3️⃣ QQ 消息示例（直播封面推送）

```
【test_name 直播监控】🎉 开播提醒
标题：新年特别直播
链接：https://live.bilibili.com/6
时间：2026-01-12 10:00:00
封面：
[CQ:image,file=https://i0.hdslb.com/bfs/live/cover.jpg]
----------------
```

## 安装要求

* Python 3.8+
* 支持的操作系统：Windows / Linux / macOS

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/X-tong2568/BTCE3.0
cd BTCE3.0
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 安装 Playwright 浏览器

```bash
playwright install chromium
```

### 4. 配置邮箱和 QQ

#### 邮箱配置（`config_email.py`）：

```python
EMAIL_USER = "your_email@qq.com"       # 发件邮箱
EMAIL_PASSWORD = "your_smtp_password"  # SMTP授权码
TO_EMAILS = ["receiver@qq.com"]        # 接收通知的邮箱列表
```

**QQ 邮箱 SMTP 授权码获取方法**：

1. 登录 QQ 邮箱 → 设置 → 账户
2. 开启 "POP3/SMTP 服务"
3. 生成授权码

#### QQ 配置（`config_qq.py`）：

1. 设置 QQ_BOT_API_URL（机器人服务地址）
2. 设置 QQ_GROUP_IDS（推送的QQ群号，字符串形式）
3. 配置访问令牌（如需要）

> 保存文件后重启程序使配置生效

### 5. 配置监控目标（动态/直播）

#### 动态监控（`dynamic.py`）：

```python
DYNAMIC_URLS = [
    "https://t.bilibili.com/动态ID1",
    "https://t.bilibili.com/动态ID2",
]
```

**获取动态ID**：打开动态页面，复制地址栏数字部分

#### 直播监控：

* 直播封面会显示在邮件和 QQ 消息中
* 仅在开播、下播、标题更新三种情况下发送通知

### 6. 获取 B站登录 Cookie

```bash
python get_cookies.py
```

扫码登录，成功后自动生成 `cookies.json`。

**隐私说明**：

* Cookie 文件仅保存在本地，不会上传
* 请妥善保管，删除时直接删除 `cookies.json`

### 7. 运行监控程序

```bash
python main.py
```

## 文件结构

```text
bili-dynamic-monitor/
├── main.py                # 主程序入口
├── config.py              # 主配置文件
├── config_email.py        # 邮箱配置
├── config_qq.py           # QQ配置
├── dynamic.py             # 监控动态列表
├── get_cookies.py         # 获取Cookie脚本
├── cookies.json           # 登录Cookie（自动生成）
├── requirements.txt       # 依赖包列表
├── README.md              # 说明文档
├── live_monitor.py        # 直播监控逻辑
├── comment_renderer.py    # 评论渲染和检测
├── email_utils.py         # 邮件发送工具
├── qq_utils.py            # QQ消息发送工具
├── health_check.py        # 健康检查
├── logger_config.py       # 日志配置
├── performance_monitor.py # 性能监控
├── status_monitor.py      # 状态监控
├── retry_decorator.py     # 重试装饰器
├── live_monitor.py        # 直播状态监控
├── self_monitor.py        # 直播状态脚本监控
├── logs/                  # 日志目录（自动生成）
├── sent_emails/           # 邮件备份（自动生成）
└── bili_pinned_comment.json # 历史记录（自动生成）
```

## 配置说明

### 主要配置项（`config.py`）

```python
# ===== 基础配置 =====
# 这些配置用于系统标识和日志记录，可以保留但简化
APP_NAME = "BTCE3.0"

# ===== 文件路径配置 =====
BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ===== 日志配置 =====
LOG_LEVEL = "INFO"
LOG_FILE_PATH = LOG_DIR / "app.log"
LOG_FORMAT = '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
MAX_LOG_SIZE_MB = 5
LOG_BACKUP_COUNT = 1

# ===== 直播监控配置 =====
LIVE_ROOM_ID = 6  # 直播间房间号 
LIVE_CHECK_INTERVAL = 15  # 直播检查间隔（秒）
LIVE_API_TIMEOUT = 10  # API请求超时时间（秒）
LIVE_MAX_RETRIES = 3  # 最大重试次数
LIVE_RETRY_DELAY = 5  # 重试延迟（秒）

# ===== 直播告警阈值 =====
LIVE_FAILURE_THRESHOLD = 10  # 连续失败阈值（P1告警）
LIVE_SUCCESS_RATE_THRESHOLD = 0.9  # 成功率阈值（P2告警）

# ===== 动态监控配置 =====
UP_NAME = "test_name"
CHECK_INTERVAL = 8  # 秒
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY = 5  # 秒

# ===== 监控配置 =====
BROWSER_RESTART_INTERVAL = 10  # 每10次循环重启浏览器
HEALTH_CHECK_INTERVAL = 15  # 每15次循环进行健康检查
TASK_TIMEOUT = 30  # 单个任务超时时间(秒)
MEMORY_THRESHOLD_MB = 500  # 内存阈值(MB)

# ===== 状态监控配置 =====
STATUS_MONITOR_INTERVAL = 7200  # 状态检查间隔（秒），2小时
NO_UPDATE_ALERT_HOURS = 28      # 无更新提醒阈值（小时）

# ===== 性能监控配置 =====
PERFORMANCE_REPORT_CYCLE_INTERVAL = 8000  # 8000轮发送一次报告

# ===== 告警阈值配置 =====
P1_TOTAL_FAILURE_THRESHOLD = 100  # 失败次数阈值（P1告警）
P2_SUCCESS_RATE_THRESHOLD = 0.8  # 成功率阈值（80%）

# ===== 系统状态检查间隔 =====
SYSTEM_STATUS_CHECK_INTERVAL = 3600  # 系统状态检查间隔（秒）

# ===== 动态链接配置 =====
try:
    from dynamic import DYNAMIC_URLS
except ImportError:
    DYNAMIC_URLS = []
    print("⚠️ 警告: 无法从 dynamic.py 导入 DYNAMIC_URLS，使用空列表")

# ===== 文件路径配置 =====
COOKIE_FILE = BASE_DIR / "cookies.json"
HISTORY_FILE = BASE_DIR / "bili_pinned_comment.json"
MAIL_SAVE_DIR = BASE_DIR / "sent_emails"

# ===== 邮件配置 =====
# 直接从独立的配置文件导入，不设置默认值
from config_email import SMTP_SERVER, SMTP_PORT, EMAIL_USER, EMAIL_PASSWORD, TO_EMAILS, STATUS_MONITOR_EMAILS

# ===== QQ推送配置 =====
# 直接从独立的配置文件导入，不设置默认值
from config_qq import QQ_GROUP_IDS, QQ_PUSH_ENABLED
```

### 邮箱配置（`config_email.py`）

* 支持 QQ、163、Gmail 等邮箱
* QQ 邮箱 SMTP: smtp.qq.com:465
* Gmail SMTP: smtp.gmail.com:587

### 动态监控配置（`dynamic.py`）

* 将要监控的动态链接添加到 `DYNAMIC_URLS` 列表

## 使用说明

### 启动监控

```bash
python main.py
```

### 停止监控

按 `Ctrl + C` 优雅停止程序

### 查看日志

```text
logs/
├── monitor.log       # 运行日志
├── error.log         # 错误日志
└── performance.log   # 性能日志
```

## 常见问题

1. **无法获取 Cookie**

   * 确保 Chromium 已安装：`playwright install chromium`
   * 检查网络连接

2. **邮件发送失败但实际收到**

   * SMTP 异步响应可能导致程序超时
   * 可增加 `email_utils.py` 中超时时间
   * 邮件备份存在则说明已生成邮件

3. **邮件完全发送失败**

   * 检查邮箱配置和授权码
   * 检查防火墙

4. **监控不到变化**

   * 动态链接格式正确
   * Cookie 是否过期

5. **内存占用过高**

   * 程序会自动重启浏览器释放内存
   * 可调整 `MEMORY_THRESHOLD_MB` 和 `BROWSER_RESTART_INTERVAL`

## 注意事项

1. 隐私安全：不要泄露 `cookies.json` 和邮箱授权码
2. 合理设置检查间隔，避免对 B站服务器造成压力
3. 定期更新 Cookie
4. 遵守 B站用户协议及相关法律法规

## 更新日志

### v3.0.0

* 支持直播状态监控（开播/下播/标题更新）
* 邮件显示完整 HTML+CSS 卡片，包含直播封面
* QQ 消息支持封面图片 CQ 码
* 保留动态置顶评论监控及邮件/QQ推送功能
* 封面变化不作为通知条件

## 技术支持

* 项目主要依赖 AI 辅助开发（ChatGPT、腾讯元宝等）
* 技术支持优先参考 AI 助手或文档

## 许可证

MIT 许可证 - 查看 [LICENSE](LICENSE)

## 免责声明

仅供学习与研究使用，使用者自行负责。
请合理设置检查频率，妥善保管 Cookie 与邮箱授权码。











