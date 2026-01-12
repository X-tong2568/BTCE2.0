#!/usr/bin/env python3
# main.py
import asyncio
import signal
import sys
import platform
import os
import time
from datetime import datetime
from logger_config import setup_logging, logger
from config import (APP_NAME, LOG_LEVEL, LOG_FILE_PATH,
                    SYSTEM_STATUS_CHECK_INTERVAL, LOG_DIR)
from monitor import Monitor
from status_monitor import status_monitor
from health_check import perform_health_checks
from email_utils import send_email
from config import TO_EMAILS, STATUS_MONITOR_EMAILS

# 尝试导入直播监控模块
try:
    from live_monitor import live_monitor
    from monitor_scheduler import live_scheduler
    from self_monitor import live_failure_counter

    LIVE_MONITOR_AVAILABLE = True
except ImportError as e:
    LIVE_MONITOR_AVAILABLE = False
    logger.warning(f"⚠️ 直播监控模块不可用: {e}")


class Application:
    """应用程序管理器"""

    def __init__(self):
        self.monitor = None
        self.status_check_task = None
        self.live_monitor_task = None
        self.setup_signal_handlers()
        self.start_time = None
        self.is_running = False

    def setup_signal_handlers(self):
        """设置信号处理器"""
        try:
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)
            if platform.system() != 'Windows':
                signal.signal(signal.SIGHUP, self.signal_handler)
        except Exception as e:
            print(f"⚠️ 信号处理器设置异常: {e}")

    def signal_handler(self, signum, frame):
        """信号处理函数"""
        signame = signal.Signals(signum).name if hasattr(signal, 'Signals') else str(signum)
        logger.info(f"📡📡 收到信号 {signame}，正在优雅退出...")
        self.is_running = False

        # 取消任务
        if self.status_check_task:
            self.status_check_task.cancel()
        if self.live_monitor_task:
            self.live_monitor_task.cancel()
        if self.monitor:
            self.monitor.is_running = False

    async def periodic_status_check(self):
        """定期状态检查任务"""
        try:
            while self.is_running:
                await asyncio.sleep(SYSTEM_STATUS_CHECK_INTERVAL)

                # 执行健康检查
                health_status = await perform_health_checks()

                # 检查动态监控状态
                await status_monitor.check_no_update_alert()

                # 检查直播监控状态（如果可用）
                if LIVE_MONITOR_AVAILABLE:
                    try:
                        live_stats = live_scheduler.get_scheduler_stats()
                        logger.info(f"📺📺 直播监控状态: {live_stats}")

                        # 检查直播监控失败计数器
                        if live_failure_counter.should_alert():
                            alert_msg = (f"【直播监控告警】连续失败次数: {live_failure_counter.consecutive_failures} "
                                         f"成功率: {live_failure_counter.get_stats()['success_rate']}")
                            await self.send_alert_email("直播监控告警", alert_msg)
                            logger.error(f"❌❌ {alert_msg}")
                    except Exception as e:
                        logger.error(f"❌❌ 检查直播监控状态失败: {e}")

                # 记录状态信息
                status_info = status_monitor.get_status_info()
                logger.info(f"📈📈 状态监控: {status_info}")

        except asyncio.CancelledError:
            logger.info("⏹⏹⏹️ 状态监控任务已取消")
        except Exception as e:
            logger.error(f"❌❌ 状态监控任务异常: {e}")

    async def send_alert_email(self, subject: str, content: str):
        """发送告警邮件"""
        try:
            email_content = f"""
            <html>
            <head><meta charset="UTF-8"></head>
            <body>
                <h2>🚨🚨 {APP_NAME} 系统告警</h2>
                <p>{content}</p>
                <p>发生时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>请及时检查系统状态！</p>
            </body>
            </html>
            """

            await asyncio.to_thread(
                send_email,
                subject=f"【系统告警】{subject}",
                content=email_content,
                to_emails=STATUS_MONITOR_EMAILS
            )
            logger.info(f"✅ 告警邮件发送成功: {subject}")
        except Exception as e:
            logger.error(f"❌❌ 发送告警邮件失败: {e}")

    async def run(self):
        """运行应用程序"""
        self.start_time = time.time()
        self.is_running = True

        # 设置日志
        setup_logging()

        # 打印启动信息
        logger.info(f"🚀🚀 启动 {APP_NAME}")
        logger.info(f"📝📝 日志级别: {LOG_LEVEL} | 日志文件: {LOG_FILE_PATH}")
        logger.info("✅✅ 配置加载完成")

        # 设置事件循环策略
        self.setup_event_loop_policy()

        try:
            # 启动状态监控任务
            self.status_check_task = asyncio.create_task(self.periodic_status_check())
            logger.info("✅✅ 系统状态监控任务已启动")

            # 启动直播监控任务（如果可用）
            if LIVE_MONITOR_AVAILABLE:
                self.live_monitor_task = asyncio.create_task(live_scheduler.start_monitoring())
                logger.info("✅✅ 直播监控任务已启动")
            else:
                logger.info("ℹ️ℹ️ 直播监控模块不可用，跳过启动")

            # 启动主监控（动态监控）
            self.monitor = Monitor()
            self.monitor.status_monitor = status_monitor
            logger.info("✅✅ 动态监控任务已启动")

            # 运行监控任务
            await self.monitor.run()

        except Exception as e:
            logger.error(f"❌❌ 应用程序错误: {e}")
            await self.send_alert_email("应用程序崩溃", f"应用程序发生未处理异常: {str(e)}")
            sys.exit(1)
        finally:
            # 优雅关闭所有任务
            await self.shutdown()

    async def shutdown(self):
        """优雅关闭所有服务"""
        logger.info("🛑 开始关闭应用程序...")

        # 停止直播监控（如果可用）
        if LIVE_MONITOR_AVAILABLE and hasattr(live_scheduler, 'is_running'):
            await live_scheduler.stop_monitoring()

        # 取消任务
        tasks = []
        if self.status_check_task and not self.status_check_task.done():
            self.status_check_task.cancel()
            tasks.append(self.status_check_task)
        if self.live_monitor_task and not self.live_monitor_task.done():
            self.live_monitor_task.cancel()
            tasks.append(self.live_monitor_task)

        # 等待任务完成
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        # 计算运行时间
        uptime = time.time() - self.start_time
        hours, remainder = divmod(uptime, 3600)
        minutes, seconds = divmod(remainder, 60)
        logger.info(f"⏱⏱ 应用程序运行时间: {int(hours)}小时 {int(minutes)}分钟 {int(seconds)}秒")
        logger.info("✅✅ 应用程序关闭完成")

    def setup_event_loop_policy(self):
        """设置事件循环策略 - Windows兼容性"""
        try:
            if platform.system() == 'Windows' and hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                logger.info("✅ 已设置 WindowsProactorEventLoopPolicy")
        except Exception as e:
            logger.warning(f"⚠️ 设置事件循环策略失败: {e}")


if __name__ == "__main__":
    # 确保日志目录存在
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

    # 创建并运行应用
    app = Application()

    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        logger.info("👋👋 用户手动中断程序")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"💥💥 未处理的顶层异常: {e}")
        sys.exit(1)
