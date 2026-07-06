#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号自动发布脚本 v3.1
图片来源: Pexels API (免费，需注册获取Key) + 备用渐变封面
"""
import os, sys, json, requests, re, time
from datetime import datetime
import tempfile, io

TMP = tempfile.gettempdir()
APPID   = os.environ.get('WECHAT_APPID', 'wx22254d05de1f5809')
SECRET  = os.environ.get('WECHAT_APPSECRET', '0990b6d901ebee8b66c1e9fe481029a4')
OPENAI  = os.environ.get('OPENAI_API_KEY', '')
PEXELS  = os.environ.get('PEXELS_API_KEY', '')
URL     = 'https://api.weixin.qq.com/cgi-bin'

# ─────────────────────────────────────────────
#  Pexels 图片搜索
# ─────────────────────────────────────────────
def pexels_search(key, n=5):
    if not PEXELS:
        return []
    try:
        r = requests.get(
            'https://api.pexels.com/v1/search',
            headers={'Authorization': PEXELS},
            params={'query': key, 'per_page': min(n, 20), 'size': 'medium'},
            timeout=15
        )
        if r.status_code == 200:
            return [p['src']['medium'] for p in r.json().get('photos', [])[:n]]
    except Exception as e:
        print(f'    [Pexels] {e}')
    return []

# ─────────────────────────────────────────────
#  下载并调整图片尺寸
# ─────────────────────────────────────────────
def download(url, size):
    from PIL import Image
    try:
        r = requests.get(url, timeout=25, stream=True)
        r.raise_for_status()
        img = Image.open(io.BytesIO(r.content))
        # RGBA/P 转 RGB
        if img.mode in ('RGBA', 'P', 'LA'):
            bg = Image.new('RGB', img.size, (255,255,255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            if img.mode == 'RGBA':
                bg.paste(img, mask=img.split()[3])
            else:
                bg.paste(img)
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        # 智能裁剪
        tw, th = size
        iw, ih = img.size
        if iw == 0 or ih == 0:
            return None
        ratio = max(tw/iw, th/ih)
        img = img.resize((int(iw*ratio), int(ih*ratio)), Image.LANCZOS)
        left = max(0, (img.size[0]-tw)//2)
        top  = max(0, (img.size[1]-th)//2)
        img = img.crop((left, top, left+tw, top+th))
        buf = io.BytesIO()
        img.save(buf, 'JPEG', quality=88, optimize=True)
        buf.seek(0)
        return buf
    except Exception as e:
        print(f'    下载失败: {e}')
        return None

# ─────────────────────────────────────────────
#  备用封面（渐变 + 标题）
# ─────────────────────────────────────────────
def fallback_cover(title, size=(900,500)):
    from PIL import Image, ImageDraw, ImageFont
    W, H = size
    img  = Image.new('RGB', (W,H))
    draw = ImageDraw.Draw(img)
    # 渐变背景
    for y in range(H):
        t = y / H
        draw.rectangle([(0,y),(W,y+1)], fill=(
            int(20+t*60), int(30+t*90), int(50+t*150)
        ))
    # 装饰线
    for x in range(0, W, 100):
        draw.rectangle([(x,0),(x+1,H)], fill=(255,255,255,40))
    # 字体
    font = None
    for fp in ['C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/simhei.ttf']:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, 48)
                break
            except:
                pass
    # 标题
    txt = title[:12] + '..' if len(title) > 12 else title
    if font:
        bbox = draw.textbbox((0,0), txt, font=font)
        w = bbox[2] - bbox[0]
        x = (W - w) // 2
        y = H//2 - 30
        # 描边
        for dx,dy in [(-2,-2),(-2,2),(2,-2),(2,2)]:
            draw.text((x+dx, y+dy), txt, fill=(0,0,0), font=font)
        draw.text((x, y), txt, fill=(255,255,255), font=font)
        # 品牌
        try:
            f2 = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 22)
            draw.text((W//2-100, H-50), '疯魔老卫 | 科技洞察', fill=(200,200,220), font=f2)
        except:
            pass
    buf = io.BytesIO()
    img.save(buf, 'JPEG', quality=88)
    buf.seek(0)
    return buf

# ─────────────────────────────────────────────
#  微信 access_token
# ─────────────────────────────────────────────
def get_token(force=False):
    tf = os.path.join(TMP, 'wechat_token.json')
    if force and os.path.exists(tf):
        try: os.remove(tf)
        except: pass
    if os.path.exists(tf) and not force:
        d = json.load(open(tf))
        if datetime.now().timestamp() < d.get('expires_at',0) - 300:
            return d['access_token']
    r = requests.get(f'{URL}/token?grant_type=client_credential&appid={APPID}&secret={SECRET}', timeout=10)
    d = r.json()
    if 'access_token' not in d:
        raise Exception(f'Token失败: {d}')
    t = d['access_token']
    json.dump({'access_token':t, 'expires_at': datetime.now().timestamp()+7200}, open(tf,'w'))
    return t

# ─────────────────────────────────────────────
#  上传封面图
# ─────────────────────────────────────────────
def upload_cover(token, title, idx=0):
    key = re.sub(r'[最新|发展|突破|分析|趋势]+', '', title).strip()[:10] or title[:8]
    print(f"    搜索: '{key} technology'")
    urls = pexels_search(key + ' technology', 3)
    buf = None
    if urls:
        for u in urls[:3]:
            print(f'    下载: {u[:80]}...')
            buf = download(u, (900,500))
            if buf:
                print('    下载成功')
                break
    if not buf:
        print('    使用备用封面')
        buf = fallback_cover(title, (900,500))
    r = requests.post(
        f'{URL}/material/add_material?access_token={token}&type=image',
        files={'media': ('cover.jpg', buf, 'image/jpeg')},
        timeout=60
    )
    res = r.json()
    if 'media_id' in res:
        return res['media_id']
    if res.get('errcode') == 40001:
        return upload_cover(get_token(True), title, idx)
    raise Exception(f'封面上传失败: {res}')

# ─────────────────────────────────────────────
#  上传文章配图
# ─────────────────────────────────────────────
def upload_article_imgs(token, title, idx=0, cnt=3):
    key = re.sub(r'[最新|发展|突破|分析|趋势]+', '', title).strip()[:10] or title[:8]
    print(f"    搜索配图: '{key} tech' (需要{cnt}张)")
    urls = pexels_search(key + ' tech', cnt+2)
    if not urls:
        print('    未找到配图')
        return []
    out = []
    for i, u in enumerate(urls[:cnt+1]):
        if len(out) >= cnt:
            break
        try:
            print(f'    配图 {len(out)+1}/{cnt}: 下载中...')
            buf = download(u, (800,450))
            if not buf:
                continue
            r = requests.post(
                f'{URL}/media/uploadimg?access_token={token}',
                files={'media': (f'art_{i}.jpg', buf, 'image/jpeg')},
                timeout=60
            )
            res = r.json()
            if 'url' in res:
                out.append(res['url'])
                print(f'    配图 {len(out)} 上传成功')
            else:
                print(f'    配图上传失败: {res}')
                if res.get('errcode') == 40001:
                    token = get_token(True)
                    r = requests.post(
                        f'{URL}/media/uploadimg?access_token={token}',
                        files={'media': (f'art_{i}.jpg', buf, 'image/jpeg')},
                        timeout=60
                    )
                    res = r.json()
                    if 'url' in res:
                        out.append(res['url'])
                        print(f'    配图 {len(out)} 重试成功')
        except Exception as e:
            print(f'    配图异常: {e}')
            continue
    return out

# ─────────────────────────────────────────────
#  热点搜索
# ─────────────────────────────────────────────
def hot_topics():
    topics = []
    try:
        r = requests.get('https://v.api.aa1.cn/api/toutiao-max/?type=科技', timeout=10)
        for item in r.json().get('data', [])[:5]:
            topics.append({'title': item.get('title',''), 'summary': item.get('summary','')})
        if len(topics) >= 5:
            return topics[:5]
    except: pass
    try:
        r = requests.get('https://api.vvhan.com/api/hotlist?type=zhihuHot', timeout=10)
        for item in r.json().get('data', [])[:5]:
            topics.append({'title': item.get('title',''), 'summary': item.get('desc','')})
        if len(topics) >= 5:
            return topics[:5]
    except: pass
    return topics[:5] if topics else [
        {'title':'AI大模型最新突破','summary':'人工智能持续突破'},
        {'title':'量子计算商业化进展','summary':'量子计算走向商用'},
        {'title':'自动驾驶技术革新','summary':'自动驾驶新突破'},
        {'title':'元宇宙产业发展趋势','summary':'元宇宙生态完善'},
        {'title':'5G应用落地案例','summary':'5G场景扩展'},
    ]

# ─────────────────────────────────────────────
#  文章生成
# ─────────────────────────────────────────────
def gen_article(topic):
    if OPENAI:
        try:
            r = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={'Authorization':f'Bearer {OPENAI}'},
                json={
                    'model':'gpt-3.5-turbo',
                    'messages':[
                        {'role':'system','content':'你是资深科技商业分析师，擅长刘润风格深度文章。'},
                        {'role':'user','content':f"根据热点撰写1500-2000字刘润风格文章：\n标题：{topic['title']}\n摘要：{topic['summary']}\n要求：开篇讲故事、2-3个案例、数据支撑、不加话题标签"}
                    ],
                    'temperature':0.7,'max_tokens':3000
                },
                timeout=60
            )
            if r.status_code == 200:
                return r.json()['choices'][0]['message']['content']
        except: pass
    t = topic['title']
    s = topic['summary']
    return (
        f"# {t}\n\n"
        f"## 引言\n\n近日，{t}成为科技圈热议话题。{s}\n\n"
        "## 现象观察\n\n从数据来看，这一领域发展速度远超预期。\n\n"
        "## 深层分析\n\n"
        "**第一，技术成熟度提升。** 关键技术指标已达到商业化门槛。\n\n"
        "**第二，用户需求升级。** 消费者追求更好用的智能产品。\n\n"
        "## 案例佐证\n\n"
        "**案例一：** 某头部公司通过技术创新，成本降低30%性能提升50%。\n\n"
        "**案例二：** 一家初创企业通过精准定位，在细分领域做到第一。\n\n"
        "## 结语\n\n"
        f"{t}是中国科技创新的缩影。保持敏锐洞察力，提升技术能力，才能抓住历史性窗口期。"
    )

# ─────────────────────────────────────────────
#  HTML 转换（含广告位）
# ─────────────────────────────────────────────
def to_html(text, imgs=None):
    lines = text.split('\n')
    out   = []
    idx   = 0
    for li, line in enumerate(lines):
        line = line.strip()
        if not line: continue
        if line.startswith('# '):
            out.append(f'<h2 style="font-size:20px;font-weight:bold;margin:24px 0 12px 0;color:rgb(15,17,21);">{line[2:].strip()}</h2>')
        elif line.startswith('## '):
            out.append(f'<h2 style="font-size:18px;font-weight:bold;margin:24px 0 12px 0;color:rgb(51,51,51);border-left:4px solid #4a90d9;padding-left:12px;">{line[3:].strip()}</h2>')
        else:
            p = line.replace('**', '<strong>').replace('**', '</strong>')
            out.append(f'<p style="margin:16px 0;color:rgb(35,35,35);font-size:16px;line-height:1.8;text-align:justify;">{p}</p>')
        # 插入配图
        if imgs and idx < len(imgs) and li > 0 and li in [len(out)//3, len(out)//2]:
            out.append(f'<section style="margin:20px 0;text-align:center;"><img src="{imgs[idx]}" style="width:100%;border-radius:8px;" /><p style="color:#999;font-size:13px;">图片来源：网络</p></section>')
            idx += 1
    while imgs and idx < len(imgs):
        out.append(f'<section style="margin:20px 0;text-align:center;"><img src="{imgs[idx]}" style="width:100%;border-radius:8px;" /><p style="color:#999;font-size:13px;">图片来源：网络</p></section>')
        idx += 1
    # 广告
    out.insert(max(3,len(out)//3), '<section style="margin:25px 0;padding:0;"><div style="background:#f7f7f7;border:1px dashed #ccc;border-radius:6px;padding:20px;text-align:center;"><p style="color:#bbb;font-size:12px;margin:0 0 8px 0;">-- 广告 --</p><p style="color:#666;font-size:14px;margin:0;font-weight:bold;">点击查看详情</p></div></section>')
    out.insert(min(len(out)*2//3, len(out)-2), '<section style="margin:25px 0;padding:0;"><div style="background:linear-gradient(to right,#f8f9fa,#fff);border-radius:8px;padding:18px;border:1px solid #eee;display:flex;align-items:center;"><div style="flex:1;"><p style="margin:0;color:#333;font-size:15px;font-weight:bold;">推荐阅读</p><p style="margin:6px 0 0 0;color:#888;font-size:13px;">关注「疯魔老卫」，每日获取最新科技洞察</p></div><div style="width:60px;height:60px;background:#4a90d9;border-radius:8px;"></div></div></section>')
    out.append('<section style="margin:25px 0;padding:18px;background:#fefce8;border-radius:8px;border-left:4px solid #eab308;"><p style="color:#854d0e;font-size:14px;margin:0 0 6px 0;font-weight:bold;">商务合作</p><p style="color:#a16207;font-size:13px;margin:0;">广告位招租 | 联系留言或私信</p></section>')
    out.append('<section style="margin:30px 0 10px 0;padding:24px;background:linear-gradient(135deg,#1e3a5f,#2d5a87);border-radius:12px;text-align:center;"><p style="color:#fff;font-size:18px;font-weight:bold;margin:0 0 10px 0;">关注「疯魔老卫」</p><p style="color:rgba(255,255,255,0.8);font-size:14px;margin:0;">每日更新科技商业洞察</p></section>')
    return '\n'.join(out)

# ─────────────────────────────────────────────
#  上传草稿
# ─────────────────────────────────────────────
def add_draft(token, title, content, thumb=''):
    art = {'title':title,'author':'老卫','digest':title[:54],'content':content,'need_open_comment':1,'only_fans_can_comment':0}
    if thumb:
        art['thumb_media_id'] = thumb
    r = requests.post(
        f'{URL}/draft/add?access_token={token}',
        data=json.dumps({'articles':[art]}, ensure_ascii=False).encode('utf-8'),
        headers={'Content-Type':'application/json'},
        timeout=30
    )
    res = r.json()
    if 'media_id' in res:
        return res['media_id']
    if res.get('errcode') == 40001:
        return add_draft(get_token(True), title, content, thumb)
    raise Exception(f'草稿上传失败: {res}')

# ─────────────────────────────────────────────
#  主流程
# ─────────────────────────────────────────────
def main():
    print('='*60)
    print('微信公众号自动发布 v3.1')
    print('='*60)
    try:
        print('\n[1/5] 获取 access_token...')
        token = get_token(True)
        print(f'  OK: {token[:20]}...')

        print('\n[2/5] 搜索科技热点...')
        topics = hot_topics()
        print(f'  找到 {len(topics)} 个话题:')
        for i,t in enumerate(topics,1):
            print(f'    {i}. {t["title"]}')

        if not PEXELS:
            print('\n[提示] PEXELS_API_KEY 未设置，将使用备用渐变封面')
            print('       免费获取: https://www.pexels.com/api/\n')

        print('\n[3/5] 搜索并上传封面图...')
        covers = {}
        for i,t in enumerate(topics[:5]):
            try:
                print(f'  [{i+1}/5] {t["title"]}')
                covers[i] = upload_cover(token, t['title'], i)
                print('  -> OK')
            except Exception as e:
                print(f'  -> 失败: {e}')
                covers[i] = ''

        print('\n[4/5] 生成文章并上传草稿...')
        ok = 0
        for i,t in enumerate(topics[:5],1):
            print(f'\n  --- 文章 {i}/5: {t["title"]} ---')
            try:
                art = gen_article(t)
                print(f'  文本生成完成 ({len(art)}字)')
                print('  搜索配图...')
                imgs = upload_article_imgs(token, t['title'], i-1, 3)
                print(f'  获得 {len(imgs)} 张配图')
                html = to_html(art, imgs)
                mid = add_draft(token, t['title'], html, covers.get(i-1,''))
                print(f'  草稿上传成功! media_id: {mid}')
                ok += 1
            except Exception as e:
                print(f'  失败: {e}')
                import traceback; traceback.print_exc()
                continue
        print(f'\n  结果: {ok}/5 篇成功')

        print('\n[5/5] 保存日志...')
        log = os.path.join(TMP, f'publish_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
        with open(log,'w',encoding='utf-8') as f:
            f.write(f'时间: {datetime.now()}\n成功: {ok}/5\n')
            for i,t in enumerate(topics[:5],1):
                f.write(f'  {i}. {t["title"]}\n')
        print('\n'+'='*60+'\n发布完成! 登录 https://mp.weixin.qq.com 查看草稿\n')
    except Exception as e:
        print(f'\n致命错误: {e}')
        import traceback; traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
