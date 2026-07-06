#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号自动发布脚本 - GitHub Actions 版本
"""

import os
import sys
import json
import requests
from datetime import datetime
import tempfile

# 临时文件目录（兼容 Windows/Linux）
TMP_DIR = tempfile.gettempdir()

# 从环境变量获取配置
WECHAT_APPID = os.environ.get('WECHAT_APPID', 'wx22254d05de1f5809')
WECHAT_APPSECRET = os.environ.get('WECHAT_APPSECRET', '0990b6d901ebee8b66c1e9fe481029a4')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

BASE_URL = "https://api.weixin.qq.com/cgi-bin"

def get_access_token():
    """获取 access_token"""
    import tempfile
    token_file = os.path.join(tempfile.gettempdir(), "wechat_token.json")
    
    # 检查缓存
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

def generate_cover_image(title, index=0):
    """使用 PIL 生成简单的封面图"""
    from PIL import Image, ImageDraw, ImageFont
    import io

    # 创建 900x500 的图片（微信推荐封面尺寸）
    img = Image.new('RGB', (900, 500), color=(45, 55, 72))
    draw = ImageDraw.Draw(img)

    # 渐变背景效果（简化版：纯色 + 装饰）
    colors = [
        (66, 153, 225),   # 蓝
        (237, 100, 166),  # 粉
        (72, 187, 120),   # 绿
        (236, 201, 75),   # 黄
        (159, 122, 234),  # 紫
    ]
    base_color = colors[index % len(colors)]

    # 绘制装饰矩形
    draw.rectangle([0, 0, 900, 500], fill=base_color)
    # 右下角深色装饰块
    draw.rectangle([600, 300, 900, 500], fill=(0, 0, 0, 80))

    # 尝试加载字体
    try:
        font_large = ImageFont.truetype("arial.ttf", 48)
        font_small = ImageFont.truetype("arial.ttf", 24)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # 绘制标题文字（截断过长标题）
    title_text = title[:12] + "..." if len(title) > 12 else title
    draw.text((50, 180), title_text, fill=(255, 255, 255), font=font_large)
    draw.text((50, 260), "疯魔老卫 | 科技洞察", fill=(200, 200, 200), font=font_small)

    # 保存到内存
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=85)
    buf.seek(0)
    return buf


def upload_cover_image(access_token, title, index=0):
    """生成并上传封面图，返回 media_id"""
    img_buf = generate_cover_image(title, index)

    url = f"{BASE_URL}/material/add_material?access_token={access_token}&type=image"
    files = {"media": ("cover.jpg", img_buf, "image/jpeg")}
    resp = requests.post(url, files=files, timeout=60)
    result = resp.json()

    if "media_id" not in result:
        raise Exception(f"上传封面图失败: {result}")

    return result["media_id"]


def search_hot_topics():
    """搜索科技热点（使用公开API）- 返回5个话题"""
    topics = []
    
    try:
        # 方法1: 使用头条API
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
        # 方法2: 使用另一个新闻源
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
    
    # 如果API都失败，使用默认话题列表
    default_topics = [
        {'title': 'AI大模型最新突破', 'url': '', 'summary': '人工智能大模型技术持续突破，应用场景不断扩展'},
        {'title': '量子计算商业化进展', 'url': '', 'summary': '量子计算技术逐步走向商业化应用'},
        {'title': '自动驾驶技术革新', 'url': '', 'summary': '自动驾驶技术迎来新一轮技术革新'},
        {'title': '元宇宙产业发展趋势', 'url': '', 'summary': '元宇宙产业生态逐步完善，应用场景丰富'},
        {'title': '5G应用落地案例', 'url': '', 'summary': '5G技术在各行业的应用案例不断涌现'}
    ]
    
    # 补充到5个
    while len(topics) < 5:
        if len(default_topics) > 0:
            topics.append(default_topics.pop(0))
        else:
            topics.append({
                'title': f'科技热点{len(topics)+1}',
                'url': '',
                'summary': '科技行业最新动态'
            })
    
    return topics[:5]

def generate_article(topic):
    """使用 OpenAI API 生成文章"""
    if not OPENAI_API_KEY:
        # 如果没有 API key，返回模板文章
        return generate_template_article(topic)
    
    prompt = f"""
    根据以下科技热点，撰写一篇刘润风格的深度文章：

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
    - 不要使用大量emoji
    - 文章末尾不加任何 #话题标签
    """

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
    else:
        return generate_template_article(topic)

def generate_template_article(topic):
    """生成模板文章（当没有 OpenAI API 时使用）"""
    return f"""
# {topic['title']}

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

{ topic['title']}不仅仅是一个热点话题，更是中国科技创新的一个缩影。在这个过程中，既有挑战，也有机遇。关键在于，我们能否抓住这个历史性的窗口期，实现从"跟跑"到"并跑"甚至"领跑"的跨越。

对于企业和从业者来说，现在需要做的是：保持敏锐的洞察力，持续提升技术能力，并在正确的时间做出正确的决策。
""".strip()

def convert_to_wechat_html(article_text):
    """将文章转换为微信公众号HTML格式"""
    # 简单转换：标题用 h2，段落用 p
    lines = article_text.split('\n')
    html_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if line.startswith('# '):
            title = line[2:].strip()
            html_lines.append(f'<h2 style="font-size:20px;font-weight:bold;margin:24px 0 12px 0;color:rgb(15,17,21);">{title}</h2>')
        elif line.startswith('## '):
            subtitle = line[3:].strip()
            html_lines.append(f'<h2 style="font-size:18px;font-weight:bold;margin:24px 0 12px 0;color:rgb(15,17,21);">{subtitle}</h2>')
        else:
            # 检查是否有加粗
            line = line.replace('**', '<strong>').replace('**', '</strong>')
            html_lines.append(f'<p style="margin:16px 0px;color:rgb(15,17,21);font-size:16px;line-height:1.75;">{line}</p>')
    
    # 插入广告位
    ad1 = '''
    <section style="margin:20px 0;padding:15px;background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);border-radius:8px;">
    <p style="color:#fff;font-size:14px;margin:0;">🔥 推荐阅读</p>
    <p style="color:rgba(255,255,255,0.9);font-size:13px;margin:8px 0 0 0;">关注「疯魔老卫」，每日获取最新科技洞察与商业分析</p>
    </section>
    '''
    
    ad2 = '''
    <section style="margin:25px 0;padding:15px;background-color:#f8f9fa;border-left:4px solid #e74c3c;border-radius:4px;">
    <p style="color:#999;font-size:13px;margin:0 0 5px 0;">— 广告位 —</p>
    <p style="color:#666;font-size:14px;margin:0;">📢 广告位招租 | 联系商务合作请留言</p>
    </section>
    '''
    
    ad3 = '''
    <section style="margin:25px 0;padding:18px;background-color:#f0f7ff;border-radius:8px;text-align:center;">
    <p style="color:#333;font-size:15px;font-weight:bold;margin:0 0 10px 0;">👇 点击下方卡片查看推荐商品 👇</p>
    <p style="color:#666;font-size:13px;margin:0;">本文由「疯魔老卫」原创出品 | 每日更新科技商业洞察</p>
    </section>
    '''
    
    # 在文章中间插入广告
    total_lines = len(html_lines)
    if total_lines > 6:
        html_lines.insert(total_lines // 3, ad1)
        html_lines.insert(total_lines * 2 // 3, ad2)
    
    html_lines.append(ad3)
    
    return '\n'.join(html_lines)

def upload_article_image(access_token, image_url):
    """上传图文消息内的图片，获取URL"""
    if image_url.startswith('http'):
        img_resp = requests.get(image_url, timeout=30)
        img_resp.raise_for_status()
        files = {"media": ("img.jpg", img_resp.content, "image/jpeg")}
    else:
        with open(image_url, 'rb') as f:
            files = {"media": ("img.jpg", f.read(), "image/jpeg")}
    
    url = f"{BASE_URL}/media/uploadimg?access_token={access_token}"
    upload_resp = requests.post(url, files=files, timeout=60)
    result = upload_resp.json()
    
    if "url" not in result:
        return None
    
    return result["url"]

def add_draft(access_token, title, content, thumb_media_id=''):
    """新建草稿"""
    url = f"{BASE_URL}/draft/add?access_token={access_token}"
    
    article = {
        "title": title,
        "author": "老卫",
        "digest": title[:50],
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

def main():
    """主函数 - 生成5篇热点文章"""
    print("=" * 60)
    print("微信公众号自动发布 - GitHub Actions 版本")
    print("=" * 60)
    
    try:
        # 1. 获取 access_token
        print("\n[1/4] 获取 access_token...")
        token = get_access_token()
        print(f"成功: {token[:20]}...")
        
        # 2. 搜索热点（获取5个话题）
        print("\n[2/4] 搜索科技热点...")
        topics = search_hot_topics()
        print(f"找到 {len(topics)} 个话题")
        
        # 3. 生成并上传5篇文章
        print("\n[3/4] 生成并上传文章...")
        success_count = 0

        # 先批量上传所有封面图
        print("  上传封面图...")
        cover_ids = {}
        for i, topic in enumerate(topics[:5]):
            try:
                mid = upload_cover_image(token, topic['title'], i)
                cover_ids[i] = mid
                print(f"  封面 {i+1}/5 上传成功")
            except Exception as e:
                print(f"  封面 {i+1} 失败: {e}")
                cover_ids[i] = ''

        for i, topic in enumerate(topics[:5], 1):
            print(f"\n--- 文章 {i}/5 ---")
            print(f"话题: {topic['title']}")

            try:
                # 生成文章
                article_text = generate_article(topic)
                print(f"  文章生成完成，字数: {len(article_text)}")

                # 转换为微信HTML
                html_content = convert_to_wechat_html(article_text)

                # 获取封面 media_id
                thumb_id = cover_ids.get(i - 1, '')

                # 上传草稿（带封面）
                media_id = add_draft(token, topic['title'], html_content, thumb_id)
                print(f"  上传成功! media_id: {media_id}")

                success_count += 1

            except Exception as e:
                print(f"  文章 {i} 失败: {e}")
                continue
        
        print(f"\n完成: {success_count}/5 篇文章上传成功")
        
        # 4. 保存日志
        print("\n[4/4] 保存执行日志...")
        log_file = os.path.join(TMP_DIR, f"publish_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        with open(log_file, 'w') as f:
            f.write(f"执行时间: {datetime.now()}\n")
            f.write(f"成功上传: {success_count}/5 篇\n")
            f.write(f"话题列表:\n")
            for i, topic in enumerate(topics[:5], 1):
                f.write(f"  {i}. {topic['title']}\n")
        
        print("\n" + "=" * 60)
        print("发布任务完成！")
        print("=" * 60)
        print(f"\n请登录 https://mp.weixin.qq.com 查看草稿")
        
    except Exception as e:
        print(f"\n错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
