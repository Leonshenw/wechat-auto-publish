#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号自动发布脚本 - GitHub Actions 版本
功能：每天自动生成5篇科技热点文章，含封面图、配图、流量主广告
"""

import os
import sys
import json
import requests
from datetime import datetime
import tempfile
import io

# 临时文件目录（兼容 Windows/Linux）
TMP_DIR = tempfile.gettempdir()

# 从环境变量获取配置
WECHAT_APPID = os.environ.get('WECHAT_APPID', 'wx22254d05de1f5809')
WECHAT_APPSECRET = os.environ.get('WECHAT_APPSECRET', '0990b6d901ebee8b66c1e9fe481029a4')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

BASE_URL = "https://api.weixin.qq.com/cgi-bin"

# ============================================================
# 中文字体加载（兼容 Windows / Linux / GitHub Actions）
# ============================================================
def get_chinese_font(size=40):
    """获取中文字体，兼容多平台"""
    from PIL import ImageFont

    # Windows 系统字体路径候选
    windows_fonts = [
        "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑
        "C:/Windows/Fonts/simhei.ttf",    # 黑体
        "C:/Windows/Fonts/simsun.ttc",    # 宋体
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    # Linux / GitHub Actions 候选
    linux_fonts = [
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",   # 文泉驿微米黑
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttf",
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    ]

    all_fonts = windows_fonts + linux_fonts

    for font_path in all_fonts:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue

    # 如果都没有，尝试下载中文字体（GitHub Actions 环境）
    try:
        font_dir = os.path.join(TMP_DIR, "fonts")
        os.makedirs(font_dir, exist_ok=True)
        font_file = os.path.join(font_dir, "NotoSansSC-Regular.ttf")

        if not os.path.exists(font_file):
            print("    [下载中文字体...]")
            # 使用 Google Noto Sans SC（开源中文字体）
            font_url = "https://github.com/google/fonts/raw/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf"
            resp = requests.get(font_url, timeout=30)
            if resp.status_code == 200:
                with open(font_file, 'wb') as f:
                    f.write(resp.content)
            else:
                # 备选：使用更小的字体文件
                alt_url = "https://raw.githubusercontent.com/StellarCN/scp_zh/master/fonts/SimHei.ttf"
                resp2 = requests.get(alt_url, timeout=30)
                with open(font_file, 'wb') as f:
                    f.write(resp2.content)

        return ImageFont.truetype(font_file, size)
    except Exception as e:
        print(f"    [警告] 无法加载中文字体: {e}")

    return ImageFont.load_default()


def generate_cover_image(title, index=0):
    """生成带中文的封面图（900x500）"""
    from PIL import Image, ImageDraw

    img = Image.new('RGB', (900, 500), color=(45, 55, 72))
    draw = ImageDraw.Draw(img)

    # 配色方案 - 科技感渐变色
    color_schemes = [
        {"bg": (30, 58, 138),   "accent": (59, 130, 246)},    # 深蓝
        {"bg": (88, 28, 135),   "accent": (168, 85, 247)},    # 深紫
        {"bg": (6, 78, 59),     "accent": (34, 197, 94)},     # 深绿
        {"bg": (120, 53, 15),   "accent": (245, 158, 11)},    # 深橙
        {"bg": (83, 31, 33),    "accent": (239, 68, 68)},     # 深红
    ]
    scheme = color_schemes[index % len(color_schemes)]

    # 绘制背景渐变效果（用矩形模拟）
    draw.rectangle([0, 0, 900, 500], fill=scheme["bg"])

    # 装饰性几何图形 - 右侧大圆
    draw.ellipse([650, 100, 1100, 550], fill=scheme["accent"])
    # 半透明覆盖
    overlay = Image.new('RGBA', (900, 500), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle([0, 350, 900, 500], fill=(0, 0, 0, 160))
    img.paste(Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB'), (0, 0))

    # 重新获取 draw 对象
    draw = ImageDraw.Draw(img)

    # 加载中文字体
    font_title = get_chinese_font(52)
    font_sub = get_chinese_font(26)
    font_brand = get_chinese_font(22)

    # 标题文字（截断）
    title_text = title[:10] + ".." if len(title) > 10 else title
    draw.text((60, 170), title_text, fill=(255, 255, 255), font=font_title)
    # 副标题线
    draw.rectangle([60, 245, 200, 249], fill=scheme["accent"])
    # 品牌名
    draw.text((60, 270), "疯魔老卫 | 科技洞察", fill=(180, 190, 200), font=font_brand)

    # 保存到 BytesIO
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=90)
    buf.seek(0)
    return buf


def generate_article_image(topic_title, index=0):
    """生成文章内配图（800x450）- 科技风格"""
    from PIL import Image, ImageDraw

    img = Image.new('RGB', (800, 450), color=(240, 243, 247))
    draw = ImageDraw.Draw(img)

    # 不同主题不同配色
    themes = [
        ("AI", (59, 130, 246), "人工智能"),
        ("Quantum", (139, 92, 246), "量子计算"),
        ("Auto", (16, 185, 129), "自动驾驶"),
        ("Meta", (236, 72, 153), "元宇宙"),
        ("5G", (245, 158, 11), "通信技术"),
    ]

    theme_name, accent_color, label = themes[index % len(themes)]

    # 背景
    draw.rectangle([0, 0, 800, 450], fill=(255, 255, 255))

    # 左侧色块装饰
    draw.rectangle([0, 0, 12, 450], fill=accent_color)

    # 中央图案 - 抽象几何
    cx, cy = 400, 200
    # 大圆环
    draw.ellipse([cx-120, cy-80, cx+120, cy+80], outline=accent_color + (100,), width=3)
    # 内部小方块
    draw.rectangle([cx-50, cy-30, cx+50, cy+30], fill=accent_color)
    # 连接线
    draw.line([cx-120, cy, cx-50, cy], fill=accent_color, width=2)
    draw.line([cx+50, cy, cx+120, cy], fill=accent_color, width=2)

    # 底部信息栏
    draw.rectangle([0, 370, 800, 450], fill=(248, 250, 252))
    draw.line([0, 370, 800, 370], fill=(226, 232, 240), width=1)

    # 加载中文字体
    font_label = get_chinese_font(28)
    font_topic = get_chinese_font(20)

    # 主题标签
    draw.text((60, 395), label, fill=(55, 65, 81), font=font_label)

    # 话题名称
    topic_short = topic_title[:16] + ".." if len(topic_title) > 16 else topic_title
    draw.text((220, 400), topic_short, fill=(107, 114, 128), font=font_topic)

    # 右下角水印
    font_watermark = get_chinese_font(16)
    draw.text((620, 415), "@疯魔老卫", fill=(156, 163, 175), font=font_watermark)

    # 保存
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=85)
    buf.seek(0)
    return buf


# ============================================================
# 微信 API 相关
# ============================================================

def get_access_token():
    """获取 access_token"""
    token_file = os.path.join(TMP_DIR, "wechat_token.json")

    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            data = json.load(f)
            if datetime.now().timestamp() < data.get('expires_at', 0) - 300:
                return data['access_token']

    url = f"{BASE_URL}/token?grant_type=client_credential&appid={WECHAT_APPID}&secret={WECHAT_APPSECRET}"
    resp = requests.get(url, timeout=10)
    result = resp.json()

    if "access_token" not in result:
        raise Exception(f"获取 access_token 失败: {result}")

    token = result["access_token"]
    expires_in = result.get("expires_in", 7200)

    with open(token_file, 'w') as f:
        json.dump({
            'access_token': token,
            'expires_at': datetime.now().timestamp() + expires_in
        }, f)

    return token


def upload_cover_image(access_token, title, index=0):
    """生成并上传封面图到素材库，返回 media_id"""
    img_buf = generate_cover_image(title, index)

    url = f"{BASE_URL}/material/add_material?access_token={access_token}&type=image"
    files = {"media": ("cover.jpg", img_buf, "image/jpeg")}
    resp = requests.post(url, files=files, timeout=60)
    result = resp.json()

    if "media_id" not in result:
        raise Exception(f"上传封面图失败: {result}")

    return result["media_id"]


def upload_article_images(access_token, title, index=0, count=3):
    """生成并上传文章配图到微信图床，返回 URL 列表"""
    urls = []
    url = f"{BASE_URL}/media/uploadimg?access_token={access_token}"

    for i in range(count):
        try:
            img_buf = generate_article_image(title, index * 3 + i)
            files = {"media": (f"article_{i}.jpg", img_buf, "image/jpeg")}
            resp = requests.post(url, files=files, timeout=60)
            result = resp.json()

            if "url" in result:
                urls.append(result["url"])
                print(f"    配图 {i+1}/{count} 上传成功")
            else:
                print(f"    配图 {i+1} 上传失败: {result}")
        except Exception as e:
            print(f"    配图 {i+1} 异常: {e}")

    return urls


# ============================================================
# 热点搜索与文章生成
# ============================================================

def search_hot_topics():
    """搜索科技热点 - 返回5个话题"""
    topics = []

    try:
        url = "https://v.api.aa1.cn/api/toutiao-max/?type=科技"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if 'data' in data:
            for item in data['data'][:5]:
                topics.append({
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'summary': item.get('summary', '')
                })
            if len(topics) >= 5:
                return topics[:5]
    except:
        pass

    try:
        url = "https://api.vvhan.com/api/hotlist?type=zhihuHot"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if 'data' in data:
            for item in data['data'][:5]:
                topics.append({
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'summary': item.get('desc', '')
                })
            if len(topics) >= 5:
                return topics[:5]
    except:
        pass

    # 默认话题
    default_topics = [
        {'title': 'AI大模型最新突破', 'url': '', 'summary': '人工智能大模型技术持续突破'},
        {'title': '量子计算商业化进展', 'url': '', 'summary': '量子计算逐步走向商用'},
        {'title': '自动驾驶技术革新', 'url': '', 'summary': '自动驾驶迎来新突破'},
        {'title': '元宇宙产业发展趋势', 'url': '', 'summary': '元宇宙生态加速完善'},
        {'title': '5G应用落地案例', 'url': '', 'summary': '5G应用场景持续扩展'},
    ]

    while len(topics) < 5:
        if default_topics:
            topics.append(default_topics.pop(0))
        else:
            topics.append({'title': f'科技热点{len(topics)+1}', 'url': '', 'summary': ''})

    return topics[:5]


def generate_article(topic):
    """生成文章内容"""
    if OPENAI_API_KEY:
        try:
            prompt = f"""根据以下科技热点，撰写一篇刘润风格的深度文章：

话题：{topic['title']}
摘要：{topic['summary']}

要求：
- 开篇从一个具体现象/故事切入（200字左右）
- 引出独特的商业或科技洞察
- 用2-3个真实案例论证观点
- 数据支撑，适当引用事实
- 结论明确，给出行动建议
- 善用小标题分隔章节
- 语言简洁有力，逻辑清晰
- 字数1500-2000字
- 不要使用emoji
- 文章末尾不加任何话题标签"""

            headers = {
                'Authorization': f'Bearer {OPENAI_API_KEY}',
                'Content-Type': 'application/json'
            }
            payload = {
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {'role': 'system', 'content': '你是一位资深科技商业分析师，擅长撰写刘润风格的深度文章。'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.7,
                'max_tokens': 3000
            }
            resp = requests.post('https://api.openai.com/v1/chat/completions',
                                headers=headers, json=payload, timeout=60)
            if resp.status_code == 200:
                return resp.json()['choices'][0]['message']['content']
        except:
            pass

    return generate_template_article(topic)


def generate_template_article(topic):
    """模板文章（无 OpenAI API 时使用）"""
    return f"""# {topic['title']}

## 引言

近日，{topic['title']}成为科技圈热议的话题。这一事件不仅仅是一个简单的新闻，更反映了当前科技行业的一些深层趋势。

## 现象观察

从数据来看，这一领域的发展速度远超预期。根据最新统计，相关市场规模在过去一年中增长了超过50%。这样的增长速度，在传统行业中是非常罕见的。

## 深层分析

为什么会出现这样的现象？我认为有三个核心原因：

**第一，技术成熟度的提升。** 经过多年的技术积累，关键技术指标已经达到了商业化应用的门槛。

**第二，用户需求的升级。** 消费者对于科技产品的期待不再停留在"能用"，而是追求"好用"和"智能"。

**第三，产业生态的完善。** 从芯片到算法，从硬件到软件，整个产业链都在快速成熟。

## 案例佐证

我们可以看几个具体的案例：

**案例一：** 某头部科技公司通过技术创新，将产品成本降低了30%，同时性能提升了50%。这种"降本增效"的能力，正是当前市场竞争的核心。

**案例二：** 一家初创企业通过精准的场景定位，在巨头的夹缝中找到了自己的生存空间，并在细分领域做到了第一。

## 未来展望

展望未来，我认为这一领域的发展将呈现三个趋势：

1. **应用深化**：从概念验证走向规模化应用
2. **生态协同**：产业链上下游的合作将更加紧密
3. **全球化竞争**：中国科技企业将在全球舞台上扮演更重要的角色

## 结语

{topic['title']}不仅仅是一个热点话题，更是中国科技创新的一个缩影。在这个过程中，既有挑战，也有机遇。关键在于，我们能否抓住这个历史性的窗口期，实现从"跟跑"到"并跑"甚至"领跑"的跨越。

对于企业和从业者来说，现在需要做的是：保持敏锐的洞察力，持续提升技术能力，并在正确的时间做出正确的决策。""".strip()


# ============================================================
# HTML 转换（含流量主广告 + 配图插入）
# ============================================================

def convert_to_wechat_html(article_text, image_urls=None):
    """
    将 Markdown 文本转换为微信 HTML 格式
    - 插入流量主广告位
    - 在合适位置插入配图
    """
    lines = article_text.split('\n')
    html_lines = []

    # 图片索引
    img_idx = 0

    for line_idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        if line.startswith('# '):
            title = line[2:].strip()
            html_lines.append(f'<h2 style="font-size:20px;font-weight:bold;margin:24px 0 12px 0;color:rgb(15,17,21);">{title}</h2>')
        elif line.startswith('## '):
            subtitle = line[3:].strip()
            html_lines.append(f'<h2 style="font-size:18px;font-weight:bold;margin:24px 0 12px 0;color:rgb(51,51,51);border-left:4px solid #4a90d9;padding-left:12px;">{subtitle}</h2>')
        else:
            # 处理加粗
            processed = line.replace('**', '<strong>').replace('**', '</strong>')
            html_lines.append(f'<p style="margin:16px 0px;color:rgb(35,35,35);font-size:16px;line-height:1.8;text-align:justify;">{processed}</p>')

        # ===== 在特定位置插入配图 =====
        if image_urls and img_idx < len(image_urls):
            total = len(html_lines)
            # 在第1个小标题后、中间段落、案例分析处插入图片
            insert_positions = [3, total // 2, total - 4]
            if line_idx > 0 and line_idx % (len(lines) // 4) == 0 and img_idx < len(image_urls):
                img_url = image_urls[img_idx]
                html_lines.append(f'''
<section style="margin:20px 0;text-align:center;">
<img src="{img_url}" style="width:100%;border-radius:8px;" />
<p style="color:#999;font-size:13px;margin:8px 0 0 0;">图片来源：疯魔老卫</p>
</section>''')
                img_idx += 1

    # 补充剩余图片（如果有）
    while image_urls and img_idx < len(image_urls):
        img_url = image_urls[img_idx]
        html_lines.append(f'''
<section style="margin:20px 0;text-align:center;">
<img src="{img_url}" style="width:100%;border-radius:8px;" />
<p style="color:#999;font-size:13px;margin:8px 0 0 0;">图片来源：疯魔老卫</p>
</section>''')
        img_idx += 1

    # ===== 流量主广告位（文中广告）=====
    traffic_ad_1 = '''
<section style="margin:25px 0;padding:0;">
<!-- 流量主广告位 - 文中Banner -->
<div style="background-color:#f7f7f7;border:1px dashed #ccc;border-radius:6px;padding:20px;text-align:center;">
<p style="color:#bbb;font-size:12px;margin:0 0 8px 0;">-- 广告 --</p>
<p style="color:#666;font-size:14px;margin:0;font-weight:bold;">点击查看详情</p>
</div>
</section>'''

    traffic_ad_2 = '''
<section style="margin:25px 0;padding:0;">
<!-- 流量主广告位 - 卡片式 -->
<div style="background:linear-gradient(to right,#f8f9fa,#fff);border-radius:8px;padding:18px;border:1px solid #eee;display:flex;align-items:center;">
<div style="flex:1;">
<p style="margin:0;color:#333;font-size:15px;font-weight:bold;">推荐阅读</p>
<p style="margin:6px 0 0 0;color:#888;font-size:13px;">关注「疯魔老卫」，每日获取最新科技洞察</p>
</div>
<div style="width:60px;height:60px;background:#4a90d9;border-radius:8px;"></div>
</div>
</section>'''

    # ===== 自定义广告位 =====
    custom_ad = '''
<section style="margin:25px 0;padding:18px;background-color:#fefce8;border-radius:8px;border-left:4px solid #eab308;">
<p style="color:#854d0e;font-size:14px;margin:0 0 6px 0;font-weight:bold;">商务合作</p>
<p style="color:#a16207;font-size:13px;margin:0;">广告位招租 | 联系方式请留言或私信</p>
</section>'''

    # ===== 底部关注引导 =====
    footer_ad = '''
<section style="margin:30px 0 10px 0;padding:24px;background:linear-gradient(135deg,#1e3a5f 0%,#2d5a87 100%);border-radius:12px;text-align:center;">
<p style="color:#fff;font-size:18px;font-weight:bold;margin:0 0 10px 0;">关注「疯魔老卫」</p>
<p style="color:rgba(255,255,255,0.8);font-size:14px;margin:0;">每日更新科技商业洞察 | 深度分析 | 行业趋势</p>
</section>

<section style="margin:15px 0;text-align:center;">
<!-- 流量主底部广告位 -->
<p style="color:#ddd;font-size:12px;margin:0;">广告</p>
</section>'''

    # 在文章中插入广告和配图
    total_lines = len(html_lines)
    if total_lines > 8:
        # 第1个位置（约1/3处）：插入流量主广告1
        pos1 = max(3, total_lines // 3)
        html_lines.insert(pos1, traffic_ad_1)

        # 第2个位置（约2/3处）：插入自定义广告
        pos2 = min(total_lines * 2 // 3, total_lines - 2)
        html_lines.insert(pos2, traffic_ad_2)

        # 第3个位置（末尾前）：插入商务合作
        html_lines.insert(total_lines, custom_ad)

    # 追加底部
    html_lines.append(footer_ad)

    return '\n'.join(html_lines)


def add_draft(access_token, title, content, thumb_media_id=''):
    """新建草稿"""
    url = f"{BASE_URL}/draft/add?access_token={access_token}"

    article = {
        "title": title,
        "author": "老卫",
        "digest": title[:54],
        "content": content,
        "need_open_comment": 1,
        "only_fans_can_comment": 0
    }

    if thumb_media_id:
        article["thumb_media_id"] = thumb_media_id

    payload = {"articles": [article]}
    headers = {"Content-Type": "application/json"}
    resp = requests.post(url, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                        headers=headers, timeout=30)
    result = resp.json()

    if "media_id" not in result:
        raise Exception(f"新建草稿失败: {result}")

    return result["media_id"]


# ============================================================
# 主流程
# ============================================================

def main():
    """主函数 - 生成5篇热点文章（含封面、配图、广告）"""
    print("=" * 60)
    print("微信公众号自动发布 v2.0")
    print("=" * 60)

    try:
        # Step 1: 获取 token
        print("\n[1/5] 获取 access_token...")
        token = get_access_token()
        print(f"  OK: {token[:20]}...")

        # Step 2: 搜索热点
        print("\n[2/5] 搜索科技热点...")
        topics = search_hot_topics()
        print(f"  找到 {len(topics)} 个话题:")
        for i, t in enumerate(topics, 1):
            print(f"    {i}. {t['title']}")

        # Step 3: 上传所有封面图
        print("\n[3/5] 生成并上传封面图...")
        cover_ids = {}
        for i, topic in enumerate(topics[:5]):
            try:
                mid = upload_cover_image(token, topic['title'], i)
                cover_ids[i] = mid
                print(f"  [{i+1}/5] 封面上传成功")
            except Exception as e:
                print(f"  [{i+1}/5] 封面失败: {e}")
                cover_ids[i] = ''

        # Step 4: 生成文章 + 配图 + 上传草稿
        print("\n[4/5] 生成文章并上传草稿...")
        success_count = 0

        for i, topic in enumerate(topics[:5], 1):
            print(f"\n  --- 文章 {i}/5: {topic['title']} ---")
            try:
                # 4a. 生成文章文本
                article_text = generate_article(topic)
                print(f"  文本生成完成 ({len(article_text)}字)")

                # 4b. 生成并上传配图
                print("  生成配图...")
                img_urls = upload_article_images(token, topic['title'], i - 1, count=3)
                print(f"  获得 {len(img_urls)} 张配图URL")

                # 4c. 转换为微信HTML（含广告+配图）
                html_content = convert_to_wechat_html(article_text, img_urls)

                # 4d. 上传草稿
                thumb_id = cover_ids.get(i - 1, '')
                media_id = add_draft(token, topic['title'], html_content, thumb_id)
                print(f"  草稿上传成功! media_id: {media_id}")
                success_count += 1

            except Exception as e:
                print(f"  失败: {e}")
                import traceback
                traceback.print_exc()
                continue

        print(f"\n  结果: {success_count}/5 篇成功")

        # Step 5: 保存日志
        print("\n[5/5] 保存执行日志...")
        log_file = os.path.join(TMP_DIR, f"publish_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"执行时间: {datetime.now()}\n")
            f.write(f"成功上传: {success_count}/5\n")
            f.write(f"话题列表:\n")
            for i, t in enumerate(topics[:5], 1):
                f.write(f"  {i}. {t['title']}\n")

        print("\n" + "=" * 60)
        print("发布任务完成！")
        print("=" * 60)
        print(f"\n请登录 https://mp.weixin.qq.com 查看草稿箱")

    except Exception as e:
        print(f"\n致命错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
