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

# 从环境变量获取配置
WECHAT_APPID = os.environ.get('WECHAT_APPID', 'wx22254d05de1f5809')
WECHAT_APPSECRET = os.environ.get('WECHAT_APPSECRET', '9kQK7UXFCfHP7CxLiTbrDzyNsCXCfPksJME5XrbPcCoD')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

BASE_URL = "https://api.weixin.qq.com/cgi-bin"

def get_access_token():
    """获取 access_token"""
    token_file = "/tmp/wechat_token.json"
    
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

def search_hot_topics():
    """搜索科技热点（使用公开API）"""
    # 使用 Toutiao API 或 News API
    # 这里使用一个简单的公开新闻源
    url = "https://v.api.aa1.cn/api/toutiao-max/?type=科技"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if 'data' in data:
            topics = []
            for item in data['data'][:5]:
                topics.append({
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'summary': item.get('summary', '')
                })
            return topics
    except:
        pass
    
    # 备选：使用默认话题
    return [{
        'title': 'AI技术发展',
        'url': '',
        'summary': '人工智能技术持续发展和应用'
    }]

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
    """主函数"""
    print("=" * 60)
    print("微信公众号自动发布 - GitHub Actions 版本")
    print("=" * 60)
    
    try:
        # 1. 获取 access_token
        print("\n[1/5] 获取 access_token...")
        token = get_access_token()
        print(f"✅ 获取成功: {token[:20]}...")
        
        # 2. 搜索热点
        print("\n[2/5] 搜索科技热点...")
        topics = search_hot_topics()
        if topics:
            topic = topics[0]
            print(f"✅ 找到话题: {topic['title']}")
        else:
            topic = {'title': '科技创新观察', 'summary': '科技行业最新动态'}
            print("⚠️  使用默认话题")
        
        # 3. 生成文章
        print("\n[3/5] 生成文章...")
        article_text = generate_article(topic)
        print(f"✅ 文章生成完成，字数: {len(article_text)}")
        
        # 4. 转换为微信HTML
        print("\n[4/5] 转换为微信HTML格式...")
        html_content = convert_to_wechat_html(article_text)
        print("✅ 转换完成")
        
        # 5. 上传草稿
        print("\n[5/5] 上传草稿到公众号...")
        # 注意：这里省略了封面图上传（需要图片）
        # 实际使用时，可以先用默认封面图或跳过
        media_id = add_draft(token, topic['title'], html_content)
        print(f"✅ 上传成功! media_id: {media_id}")
        
        # 保存日志
        log_file = f"/tmp/publish_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(log_file, 'w') as f:
            f.write(f"执行时间: {datetime.now()}\n")
            f.write(f"文章标题: {topic['title']}\n")
            f.write(f"草稿 media_id: {media_id}\n")
            f.write("状态: 成功\n")
        
        print("\n" + "=" * 60)
        print("🎉 发布任务完成！")
        print("=" * 60)
        print(f"\n请登录 https://mp.weixin.qq.com 查看草稿")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
