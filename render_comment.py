# render_comment.py
import time
import asyncio
import random
from bs4 import BeautifulSoup
from config import UP_NAME
from logger_config import logger
from datetime import datetime


class CommentRenderer:
    """评论渲染和变化检测类"""

    def __init__(self):
        """初始化颜色生成器"""
        # 定义对比色组合，每对都是对比色
        self.color_gradients = [
            # 红绿渐变
            ("#FF5252", "#4CAF50"),  # 红色 -> 绿色
            ("#E53935", "#66BB6A"),  # 深红 -> 浅绿

            # 蓝橙渐变
            ("#2196F3", "#FF9800"),  # 蓝色 -> 橙色
            ("#1565C0", "#FF5722"),  # 深蓝 -> 深橙

            # 紫黄渐变
            ("#9C27B0", "#FFEB3B"),  # 紫色 -> 黄色
            ("#7B1FA2", "#FFD600"),  # 深紫 -> 金黄

            # 青粉渐变
            ("#00BCD4", "#E91E63"),  # 青色 -> 粉色
            ("#0097A7", "#C2185B"),  # 深青 -> 深粉

            # 青橙渐变
            ("#009688", "#FF9800"),  # 青色 -> 橙色
            ("#00695C", "#F57C00"),  # 深青 -> 深橙

            # 紫绿渐变
            ("#673AB7", "#8BC34A"),  # 紫色 -> 浅绿
            ("#512DA8", "#689F38"),  # 深紫 -> 深绿

            # 橙蓝渐变
            ("#FF9800", "#2196F3"),  # 橙色 -> 蓝色
            ("#F57C00", "#1976D2"),  # 深橙 -> 深蓝

            # 粉青渐变
            ("#E91E63", "#00BCD4"),  # 粉色 -> 青色
            ("#C2185B", "#0097A7"),  # 深粉 -> 深青

            # 红蓝渐变
            ("#F44336", "#3F51B5"),  # 红色 -> 蓝色
            ("#D32F2F", "#303F9F"),  # 深红 -> 深蓝

            # 黄紫渐变
            ("#FFEB3B", "#9C27B0"),  # 黄色 -> 紫色
            ("#FBC02D", "#7B1FA2"),  # 深黄 -> 深紫
        ]

    def _get_random_gradient(self):
        """获取随机双色渐变（对比色）"""
        primary, secondary = random.choice(self.color_gradients)
        logger.info(f"🎨 使用对比色渐变: {primary} -> {secondary}")
        return primary, secondary

    @staticmethod
    def extract_text_from_html(html_content: str) -> str:
        """从HTML提取纯文字"""
        if not html_content:
            return ""

        soup = BeautifulSoup(html_content, "html.parser")
        return soup.get_text(strip=True)

    async def get_pinned_comment(self, page, dynamic_id):
        """
        抓取置顶评论：
        - pinned_comment_html: 评论 HTML（含文字+表情）
        - comment_images: 评论区上传的图片 URL 列表
        """
        await page.goto(f"https://t.bilibili.com/{dynamic_id}")

        try:
            await page.wait_for_selector("bili-comment-thread-renderer", timeout=15000)
        except:
            return "未找到置顶评论", []

        # 模拟滚动加载更多评论
        for _ in range(5):
            await page.evaluate("window.scrollBy(0, 1000)")
            await asyncio.sleep(1)

        pinned_comment_html = None
        comment_images = []

        comment_items = await page.query_selector_all("bili-comment-thread-renderer")
        for item in comment_items:
            top_tag = await item.query_selector("i#top")
            if top_tag:
                # 文字+表情 HTML
                content_element = await item.query_selector("bili-rich-text p#contents")
                if content_element:
                    pinned_comment_html = await content_element.inner_html()

                # 评论区上传图片 - 修复图片获取逻辑
                pics_renderer = await item.query_selector("bili-comment-pictures-renderer")
                if pics_renderer:
                    try:
                        # 使用 evaluate 方法访问 shadow DOM
                        img_src_list = await pics_renderer.evaluate(
                            """(el) => {
                                const imgs = [];
                                const shadow = el.shadowRoot;
                                if (shadow) {
                                    const img_tags = shadow.querySelectorAll('img');
                                    img_tags.forEach(img => {
                                        let src = img.src;
                                        if (src.startsWith('//')) {
                                            src = 'https:' + src;
                                        }
                                        // 移除图片参数，获取原始图片
                                        if (src.includes('@')) {
                                            src = src.split('@')[0];
                                        }
                                        imgs.push(src);
                                    });
                                }
                                return imgs;
                            }"""
                        )
                        comment_images.extend(img_src_list)
                    except Exception as e:
                        logger.error(f"❌❌ 通过shadow DOM获取图片失败: {e}")

                        # 备用方法：尝试直接获取图片元素
                        try:
                            img_elements = await pics_renderer.query_selector_all('img')
                            for img in img_elements:
                                src = await img.get_attribute('src')
                                if src:
                                    if src.startswith('//'):
                                        src = 'https:' + src
                                    if '@' in src:
                                        src = src.split('@')[0]
                                    if src not in comment_images:
                                        comment_images.append(src)
                        except Exception as e2:
                            logger.error(f"❌❌ 直接获取图片元素失败: {e2}")

                break

        if pinned_comment_html:
            return pinned_comment_html.strip(), comment_images
        return "未找到置顶评论", []

    async def detect_comment_change(self, current_html, current_images, last_html, last_images):
        """检测评论变化"""
        try:
            current_text = self.extract_text_from_html(current_html)
            last_text = self.extract_text_from_html(last_html)

            logger.info(f"当前置顶评论: {current_text}")
            logger.info(f"上次记录: {last_text if last_text else '无记录'}")

            # 检测文字变化
            if last_text and current_text != last_text:
                logger.info("🔔 检测到置顶评论文字变化！")
                return True

            # 检测图片变化
            if set(current_images) != set(last_images):
                logger.info("🔔 检测到置顶评论图片变化！")
                return True

            return False

        except Exception as e:
            logger.error(f"❌ 检测评论变化失败: {e}")
            return False

    def render_email_content(self, dynamic_id, current_html, current_images, last_html, last_images, current_time=None):
        """渲染邮件内容 - 修复图片显示问题，将跳转按钮放在单独区域，并使用随机对比色渐变"""
        try:
            if current_time is None:
                current_time = time.strftime('%Y-%m-%d %H:%M:%S')

            # 获取随机对比色渐变
            primary_color, secondary_color = self._get_random_gradient()

            email_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>{UP_NAME} 动态置顶评论更新通知</title>
                <style>
                    body {{
                        font-family: 'Microsoft YaHei', Arial, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background-color: #f5f5f5;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background-color: white;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        overflow: hidden;
                    }}
                    .header {{
                        background: linear-gradient(135deg, {primary_color}, {secondary_color});
                        color: white;
                        padding: 20px;
                        text-align: center;
                    }}
                    .header h1 {{
                        margin: 0;
                        font-size: 24px;
                        text-shadow: 1px 1px 3px rgba(0,0,0,0.2);
                    }}
                    .header-gradient-bar {{
                        height: 5px;
                        background: linear-gradient(90deg, {primary_color}, {secondary_color});
                        margin-top: 10px;
                    }}
                    .content {{
                        padding: 30px;
                    }}
                    .info-section {{
                        background-color: #f9f9f9;
                        padding: 20px;
                        border-radius: 8px;
                        margin-bottom: 20px;
                        border-left: 4px solid {primary_color};
                        border-right: 4px solid {secondary_color};
                    }}
                    .comment-content {{
                        border: 1px solid #ddd;
                        padding: 15px;
                        border-radius: 5px;
                        white-space: pre-wrap;
                        word-break: break-all;
                        margin-top: 10px;
                        line-height: 1.5;
                    }}
                    .current-comment {{
                        background-color: #f0f8ff;
                        border-left: 4px solid {primary_color};
                        border-right: 4px solid {secondary_color};
                    }}
                    .previous-comment {{
                        background-color: #f0f0f0;
                        border-left: 4px solid {primary_color};
                        border-right: 4px solid {secondary_color};
                    }}
                    .images-container {{
                        display: flex;
                        flex-wrap: wrap;
                        gap: 10px;
                        margin-top: 10px;
                    }}
                    .image-item {{
                        max-width: 300px;
                        max-height: 300px;
                        object-fit: contain;
                        border-radius: 5px;
                        border: 1px solid #ddd;
                    }}
                    .btn {{
                        display: inline-block;
                        margin-top: 10px;
                        background: linear-gradient(135deg, {primary_color}, {secondary_color});
                        color: #fff;
                        padding: 12px 24px;
                        border-radius: 5px;
                        text-decoration: none;
                        font-weight: bold;
                        transition: all 0.3s ease;
                        border: none;
                        cursor: pointer;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                    }}
                    .btn:hover {{
                        transform: translateY(-2px);
                        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                    }}
                    .action-section {{
                        text-align: center;
                        padding: 25px;
                        background: linear-gradient(135deg, #f9f9f9, #f0f0f0);
                        border-radius: 8px;
                        margin: 20px 0;
                        border: 2px solid transparent;
                        border-image: linear-gradient(135deg, {primary_color}, {secondary_color});
                        border-image-slice: 1;
                    }}
                    .action-section p {{
                        font-size: 16px;
                        margin-bottom: 15px;
                        color: #333;
                    }}
                    .footer {{
                        text-align: center;
                        color: #999;
                        font-size: 12px;
                        margin-top: 20px;
                        padding: 20px;
                        border-top: 1px solid #eee;
                    }}
                    .time-badge {{
                        display: inline-block;
                        background: linear-gradient(135deg, {primary_color}, {secondary_color});
                        color: white;
                        padding: 4px 8px;
                        border-radius: 3px;
                        font-size: 12px;
                        margin-left: 5px;
                    }}
                    .key-badge {{
                        display: inline-block;
                        background: linear-gradient(135deg, {primary_color}, {secondary_color});
                        color: white;
                        padding: 4px 8px;
                        border-radius: 3px;
                        font-size: 16px;
                        margin-left: 5px;
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>{UP_NAME} 动态置顶评论更新通知</h1>
                        <div class="header-gradient-bar"></div>
                    </div>

                    <div class="content">
                        <div class="info-section">
                            <span class="time-badge">📱 监测动态：</span></p>
                            <a href="https://t.bilibili.com/{dynamic_id}">
                            https://t.bilibili.com/{dynamic_id}</a></p>
                            <p><strong><span class="time-badge">⏰ 检测时间：</span></p> </strong>{current_time}
                        </div>

                        <div class="info-section">
                            <span class="key-badge">✨ 新置顶评论： ✨</span></p>
                            <div class="comment-content current-comment">
                                {current_html if current_html else "无置顶评论"}
                            </div>
            """

            # ✅ 新置顶评论图片
            if current_images:
                email_body += '<div class="images-container">'
                for img_url in current_images:
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    elif not img_url.startswith(('http://', 'https://')):
                        img_url = 'https:' + img_url
                    email_body += f'<img class="image-item" src="{img_url}" alt="评论图片">'
                email_body += '</div>'

            email_body += f"""
                        </div>

                        <div class="info-section">
                            <span class="key-badge">📄 原置顶评论： 📄</span></p>
                            <div class="comment-content previous-comment">
                                {last_html if last_html else "无原置顶评论"}
                            </div>
            """

            # ✅ 原置顶评论图片
            if last_images:
                email_body += '<div class="images-container">'
                for img_url in last_images:
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    elif not img_url.startswith(('http://', 'https://')):
                        img_url = 'https:' + img_url
                    email_body += f'<img class="image-item" src="{img_url}" alt="原评论图片">'
                email_body += '</div>'

            email_body += f"""
                        </div>

                        <!-- 独立的按钮区域 -->
                        <div class="action-section">
                            <p>点击下方按钮查看最新动态：</p>
                            <a class="btn" href="https://t.bilibili.com/{dynamic_id}?comment_on=1" target="_blank">
                                🔍 前往B站查看动态
                            </a>
                        </div>
                    </div>

                    <div class="footer">
                        <p>此邮件由动态监控系统自动发送，请勿回复</p>
                        <p>检测时间: {current_time}</p>
                         <p>本次随机主题色: {primary_color} → {secondary_color}</p>
                    </div>
                </div>
            </body>
            </html>
            """
            return email_body
        except Exception as e:
            logger.error(f"❌ 渲染邮件内容失败: {e}")
            return f"<html><body><h1>渲染邮件内容出错: {e}</h1></body></html>"

    def generate_qq_message(self, up_name: str, dynamic_id: str, current_html: str, current_time: str,
                            current_images: list) -> str:
        """生成QQ群推送消息（纯文本，表情转为alt文字，图片使用CQ码）"""
        try:
            # 使用BeautifulSoup处理HTML，将表情图片替换为alt文字
            soup = BeautifulSoup(current_html, "html.parser")

            # 找到所有表情图片，替换为alt属性中的文字
            for img in soup.find_all("img"):
                alt_text = img.get("alt", "")
                if alt_text:
                    # 用alt文字替换图片
                    img.replace_with(alt_text)
                else:
                    # 如果没有alt属性，移除图片
                    img.decompose()

            # 提取纯文本内容
            text_content = soup.get_text(strip=True)

            # 生成QQ消息
            qq_message = f"【{up_name}】瞳瞳空间更新啦~\n"
            qq_message += f"{text_content}\n"

            # 添加图片（如果有）
            if current_images:
                qq_message += "📸 图片：\n"
                # 限制最多发送3张图片，避免消息过长
                for i, img_url in enumerate(current_images[:3]):
                    # 使用CQ码发送图片
                    qq_message += f"[CQ:image,file={img_url}]\n"
                if len(current_images) > 3:
                    qq_message += f"... 还有 {len(current_images) - 3} 张图片\n"

            qq_message += "----------------\n"
            qq_message += f"📅 检测时间: {current_time}\n"
            qq_message += f"🔗 监测动态: https://t.bilibili.com/{dynamic_id}\n"
            qq_message += "----------------"

            return qq_message

        except Exception as e:
            logger.error(f"❌ 生成QQ消息失败: {e}")
            # 备用消息格式
            backup_msg = f"【{up_name}】置顶评论更新通知\n动态: {dynamic_id}\n时间: {current_time}"
            if current_images:
                backup_msg += f"\n包含 {len(current_images)} 张图片"
            return backup_msg
