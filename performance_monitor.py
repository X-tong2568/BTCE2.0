import asyncio
import psutil
import time
import math
from datetime import datetime
from logger_config import logger
from email_utils import send_email
from config_email import STATUS_MONITOR_EMAILS
from config import (
    P1_TOTAL_FAILURE_THRESHOLD,
    P2_SUCCESS_RATE_THRESHOLD,
    PERFORMANCE_REPORT_CYCLE_INTERVAL
)


#| 邮件类型      | 主题语义    | 主色            |
#| --------- | ------- | ------------- |
#| **P1 告警** | 严重 / 紧急 | 深橙色 `#E65100` |
#| **P2 告警** | 警告 / 风险 | 琥珀色 `#F9A825` |
#| **性能报告**  | 稳定 / 中性 | 青绿色 `#00796B` |


class PerformanceMonitor:
    """性能监控器：修复P1/P2告警触发问题"""

    def __init__(self):
        self.total_cycles = 0
        self.cumulative_success = 0  # 累计成功轮次
        self.cumulative_failure = 0  # 新增：累计失败轮次
        self.memory_peak = 0
        self.cycle_durations = []
        self.start_time = time.time()
        self.last_alert_time = 0
        self.last_report_cycle = 0
        self.p1_alert_sent = False
        self.p2_alert_sent = False
        self.report_sent = False

        logger.info("📊 性能监控器初始化完成（修复P1/P2触发逻辑）")
        logger.info(f"  - 报告间隔: 每{PERFORMANCE_REPORT_CYCLE_INTERVAL}轮")
        logger.info(f"  - P1告警: 失败次数 ≥ {P1_TOTAL_FAILURE_THRESHOLD}")
        logger.info(f"  - P2告警: 成功率 < {P2_SUCCESS_RATE_THRESHOLD * 100:.0f}%")

    async def record_memory_usage(self):
        """记录当前内存使用（MB）"""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            if memory_mb > self.memory_peak:
                self.memory_peak = memory_mb
            return memory_mb
        except Exception as e:
            logger.error(f"❌ 记录内存使用失败: {e}")
            return 0

    def record_cycle(self, cycle_number, success, duration=None):
        """记录单轮结果，并触发条件检查"""
        try:
            # 更新总轮次
            self.total_cycles = cycle_number

            # 更新累计成功/失败轮次
            if success:
                self.cumulative_success += 1
            else:
                self.cumulative_failure += 1  # 新增：记录失败次数

            # 记录轮次时长
            if duration is not None:
                self.cycle_durations.append({
                    'cycle': cycle_number,
                    'duration': duration,
                    'timestamp': datetime.now(),
                    'success': success
                })

            # 计算当前状态
            total = self.total_cycles
            success_count = self.cumulative_success
            failure_count = self.cumulative_failure
            success_rate = success_count / total if total > 0 else 1.0

            # 调试日志：显示当前状态
            logger.debug(
                f"📊 监控状态: 总轮次={total}, 成功={success_count}, 失败={failure_count}, 成功率={success_rate:.2%}")

            # 检查告警条件
            self._check_conditions(total, success_count, failure_count, success_rate)

        except Exception as e:
            logger.error(f"❌ 记录轮次结果失败: {e}")

    def _check_conditions(self, total, success, failure, success_rate):
        """基于当前累计值检查告警条件（修复核心逻辑）"""
        try:
            # 调试日志：显示检查时的详细状态
            logger.debug(
                f"🔍 检查条件: 失败={failure}/{P1_TOTAL_FAILURE_THRESHOLD}, 成功率={success_rate:.2%}/{P2_SUCCESS_RATE_THRESHOLD:.0%}")

            # 1. P1: 累计失败次数达到阈值（使用累计失败次数）
            if failure >= P1_TOTAL_FAILURE_THRESHOLD and not self.p1_alert_sent:
                logger.error(f"🚨 P1告警条件满足: 失败次数={failure} (阈值: {P1_TOTAL_FAILURE_THRESHOLD})")
                logger.info(f"📊 P1告警详情: 总轮次={total}, 成功={success}, 失败={failure}")
                asyncio.create_task(self._send_p1_alert(total, failure))
                self.p1_alert_sent = True
                self.last_alert_time = time.time()
            elif failure < P1_TOTAL_FAILURE_THRESHOLD and self.p1_alert_sent:
                logger.info(f"🔄 P1告警重置: 失败次数={failure} < 阈值={P1_TOTAL_FAILURE_THRESHOLD}")
                self.p1_alert_sent = False

            # 2. P2: 成功率低于阈值（使用当前累计成功率）
            if success_rate < P2_SUCCESS_RATE_THRESHOLD and not self.p2_alert_sent:
                logger.error(f"🚨 P2告警条件满足: 成功率={success_rate:.2%} (阈值: {P2_SUCCESS_RATE_THRESHOLD:.0%})")
                logger.info(f"📊 P2告警详情: 总轮次={total}, 成功={success}, 失败={failure}")
                asyncio.create_task(self._send_p2_alert(total, success_rate))
                self.p2_alert_sent = True
                self.last_alert_time = time.time()
            elif success_rate >= P2_SUCCESS_RATE_THRESHOLD and self.p2_alert_sent:
                logger.info(f"🔄 P2告警重置: 成功率={success_rate:.2%} >= 阈值={P2_SUCCESS_RATE_THRESHOLD:.0%}")
                self.p2_alert_sent = False

            # 3. 定期性能报告
            if total - self.last_report_cycle >= PERFORMANCE_REPORT_CYCLE_INTERVAL and not self.report_sent:
                logger.info(f"📧 满足报告发送条件: 第{total}轮 (上次报告: 第{self.last_report_cycle}轮)")
                asyncio.create_task(self._send_report(total))
                self.report_sent = True
                self.last_report_cycle = total
            elif total < self.last_report_cycle + PERFORMANCE_REPORT_CYCLE_INTERVAL and self.report_sent:
                self.report_sent = False  # 重置标志允许下次发送

        except Exception as e:
            logger.error(f"❌ 检查条件失败: {e}")

    async def _send_p1_alert(self, total_cycles, failure_count):
        """发送P1告警邮件"""
        try:
            subject = f"🚨 P1告警: 失败次数达 {failure_count} 次 (第{total_cycles}轮)"
            content = self._generate_p1_alert_content(total_cycles, failure_count)

            logger.info(f"📤 正在发送P1告警邮件: {subject}")
            success = await asyncio.to_thread(
                send_email,
                subject=subject,
                content=content,
                to_emails=STATUS_MONITOR_EMAILS
            )
            if success:
                logger.info("✅ P1告警邮件发送成功")
            else:
                logger.error("❌ P1告警邮件发送失败")
        except Exception as e:
            logger.error(f"❌ 发送P1告警邮件异常: {e}")

    async def _send_p2_alert(self, total_cycles, success_rate):
        """发送P2告警邮件"""
        try:
            subject = f"⚠️ P2告警: 成功率过低 {success_rate:.1%} (第{total_cycles}轮)"
            content = self._generate_p2_alert_content(total_cycles, success_rate)

            logger.info(f"📤 正在发送P2告警邮件: {subject}")
            success = await asyncio.to_thread(
                send_email,
                subject=subject,
                content=content,
                to_emails=STATUS_MONITOR_EMAILS
            )
            if success:
                logger.info("✅ P2告警邮件发送成功")
            else:
                logger.error("❌ P2告警邮件发送失败")
        except Exception as e:
            logger.error(f"❌ 发送P2告警邮件异常: {e}")

    async def _send_report(self, total_cycles):
        """发送定期性能报告"""
        try:
            subject = f"📊 ttkj-monitor性能报告 - 第{total_cycles}轮"
            content = self._generate_report_content(total_cycles)

            logger.info(f"📤 正在发送性能报告邮件: {subject}")
            success = await asyncio.to_thread(
                send_email,
                subject=subject,
                content=content,
                to_emails=STATUS_MONITOR_EMAILS
            )
            if success:
                logger.info("✅ 性能报告邮件发送成功")
                self.report_sent = False  # 重置标志允许下次发送
            else:
                logger.error("❌ 性能报告邮件发送失败")
        except Exception as e:
            logger.error(f"❌ 发送性能报告邮件异常: {e}")

    def _generate_p1_alert_content(self, total_cycles, failure_count):
        success = self.cumulative_success
        success_rate = success / total_cycles if total_cycles > 0 else 0

        recent_failures = []
        for record in reversed(self.cycle_durations):
            if not record['success']:
                recent_failures.append(record['timestamp'].strftime('%H:%M:%S'))
            if len(recent_failures) >= 5:
                break

        theme = "#E65100"

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Microsoft YaHei', Arial, sans-serif;
                    background: #f5f5f5;
                    padding: 20px;
                }}
                .card {{
                    max-width: 600px;
                    margin: auto;
                    background: #fff;
                    border-radius: 10px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.12);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, {theme}, #BF360C);
                    color: white;
                    padding: 20px;
                    text-align: center;
                }}
                .content {{
                    padding: 24px;
                }}
                .stat {{
                    background: #fff3e0;
                    padding: 12px;
                    border-radius: 6px;
                    margin-bottom: 12px;
                }}
                ul {{
                    padding-left: 18px;
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="header">
                    <h2>🚨 P1 严重告警</h2>
                    <p>累计失败次数超出安全阈值</p>
                </div>

                <div class="content">
                    <div class="stat"><strong>失败次数：</strong>{failure_count}</div>
                    <div class="stat"><strong>当前轮次：</strong>{total_cycles}</div>
                    <div class="stat"><strong>成功率：</strong>{success_rate:.1%}</div>

                    <h4>最近失败时间</h4>
                    <ul>
                        {''.join(f'<li>{t}</li>' for t in recent_failures)}
                    </ul>

                    <p><strong>⚠️ 请立即检查系统运行状态。</strong></p>
                </div>
            </div>
        </body>
        </html>
        """

    def _generate_p2_alert_content(self, total_cycles, success_rate):
        success = self.cumulative_success
        failure = self.cumulative_failure

        recent = self.cycle_durations[-10:] if len(self.cycle_durations) >= 10 else self.cycle_durations
        recent_success = sum(1 for r in recent if r['success'])
        recent_rate = recent_success / len(recent) if recent else 0

        theme = "#F9A825"

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Microsoft YaHei', Arial, sans-serif;
                    background: #f5f5f5;
                    padding: 20px;
                }}
                .card {{
                    max-width: 600px;
                    margin: auto;
                    background: #fff;
                    border-radius: 10px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, {theme}, #F57F17);
                    color: white;
                    padding: 20px;
                    text-align: center;
                }}
                .content {{
                    padding: 24px;
                }}
                .stat {{
                    background: #fffde7;
                    padding: 12px;
                    border-radius: 6px;
                    margin-bottom: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="header">
                    <h2>⚠️ P2 性能告警</h2>
                    <p>成功率低于预期阈值</p>
                </div>

                <div class="content">
                    <div class="stat"><strong>总体成功率：</strong>{success_rate:.2%}</div>
                    <div class="stat"><strong>最近成功率：</strong>{recent_rate:.2%}</div>
                    <div class="stat"><strong>失败轮次：</strong>{failure}</div>

                    <h4>建议排查项</h4>
                    <ul>
                        <li>Cookie 是否失效</li>
                        <li>网络波动</li>
                        <li>反爬策略变化</li>
                        <li>浏览器实例稳定性</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """

    def _generate_report_content(self, total_cycles):
        uptime_hours = (time.time() - self.start_time) / 3600
        success = self.cumulative_success
        failure = self.cumulative_failure
        success_rate = success / total_cycles if total_cycles > 0 else 0

        avg = sum(r['duration'] for r in self.cycle_durations) / len(
            self.cycle_durations) if self.cycle_durations else 0
        recent = self.cycle_durations[-10:] if len(self.cycle_durations) >= 10 else self.cycle_durations
        recent_avg = sum(r['duration'] for r in recent) / len(recent) if recent else 0

        theme = "#00796B"

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Microsoft YaHei', Arial, sans-serif;
                    background: #f5f5f5;
                    padding: 20px;
                }}
                .card {{
                    max-width: 700px;
                    margin: auto;
                    background: #fff;
                    border-radius: 10px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, {theme}, #004D40);
                    color: white;
                    padding: 20px;
                    text-align: center;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 10px;
                }}
                th {{
                    background: #e0f2f1;
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="header">
                    <h2>📊 性能运行报告</h2>
                    <p>第 {total_cycles} 轮</p>
                </div>

                <table>
                    <tr><th>指标</th><th>数值</th></tr>
                    <tr><td>运行时间</td><td>{uptime_hours:.1f} 小时</td></tr>
                    <tr><td>成功率</td><td>{success_rate:.2%}</td></tr>
                    <tr><td>失败轮次</td><td>{failure}</td></tr>
                    <tr><td>平均耗时</td><td>{avg:.1f}s</td></tr>
                    <tr><td>最近10轮</td><td>{recent_avg:.1f}s</td></tr>
                </table>
            </div>
        </body>
        </html>
        """

    async def periodic_report(self, interval_minutes=60):
        """按时间定期输出简要性能日志（非邮件）"""
        while True:
            try:
                await asyncio.sleep(interval_minutes * 60)
                memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
                uptime_hours = (time.time() - self.start_time) / 3600
                total = self.total_cycles
                success_rate = self.cumulative_success / total if total > 0 else 0
                logger.info(
                    f"📊 定期性能摘要: 运行{uptime_hours:.1f}小时, 轮次{total}, "
                    f"成功率{success_rate:.1%}, 失败{self.cumulative_failure}次, "
                    f"内存{memory_mb:.1f}MB, P1状态={'已触发' if self.p1_alert_sent else '正常'}, "
                    f"P2状态={'已触发' if self.p2_alert_sent else '正常'}"
                )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 定期性能摘要异常: {e}")


# 全局实例
performance_monitor = PerformanceMonitor()
