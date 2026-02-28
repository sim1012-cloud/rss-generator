import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import datetime
import time

def get_ig_feed(usernames):
    fg = FeedGenerator()
    fg.title('Instagram 聚合动态 (Picuki 镜像源)')
    fg.link(href='https://www.picuki.com', rel='alternate')
    fg.description('通过 GitHub Actions 抓取镜像站生成的 IG 图文 RSS')
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/'
    }
    
    run_timestamp = str(int(time.time()))
    
    for username in usernames:
        print(f"正在处理账号: {username}")
        url = f'https://www.picuki.com/profile/{username}'
        
        try:
            time.sleep(2) # 延时防封
            res = requests.get(url, headers=headers, timeout=15)
            
            if res.status_code != 200:
                print(f"  -> [{username}] 请求失败，状态码: {res.status_code}")
                continue
                
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 兼容 Picuki 常见的帖子容器类名
            posts = soup.find_all('div', class_='box-photo') or soup.find_all('li', class_='box-photo')
            
            if not posts:
                print(f"  -> [{username}] 未找到帖子内容，可能遭遇验证码或页面改版。")
                continue
                
            # 每个账号仅提取最新 5 条，控制 XML 体积
            for post in posts[:5]:
                link_tag = post.find('a')
                link = link_tag['href'] if link_tag and link_tag.has_attr('href') else f"https://www.picuki.com/profile/{username}"
                
                img_tag = post.find('img')
                img_src = img_tag['src'] if img_tag and img_tag.has_attr('src') else ""
                
                desc_tag = post.find('div', class_='photo-description')
                desc_text = desc_tag.text.strip() if desc_tag else "无文字描述"
                
                fe = fg.add_entry()
                # 标题为账号名 + 截断的摘要
                short_desc = desc_text[:30] + "..." if len(desc_text) > 30 else desc_text
                fe.title(f"[{username}] {short_desc}")
                
                # 击穿 Inoreader 缓存的时间戳策略
                unique_url = link + "?v=" + run_timestamp
                fe.link(href=unique_url)
                fe.id(unique_url)
                
                # 拼装适用于卡片视图的 HTML 富文本
                img_html = f'<div style="margin-bottom: 15px;"><img src="{img_src}" style="max-width: 100%; border-radius: 6px;" /></div>' if img_src else ""
                html_content = f'{img_html}<p style="font-size: 14px; color: #444; line-height: 1.6; margin: 0;">{desc_text}</p>'
                
                fe.description(html_content)
                fe.pubDate(datetime.datetime.now(datetime.timezone.utc))
                
            print(f"  -> [{username}] 成功提取完毕。")
                
        except Exception as e:
            print(f"  -> [{username}] 解析出错: {e}")
            
    fg.rss_file('instagram.xml')
    print("====== IG RSS 源生成完毕 ======")

if __name__ == "__main__":
    # 在这里可以随时增删你需要监控的 IG 账号
    target_accounts = ['wired', 'pyoeunjizzang']
    get_ig_feed(target_accounts)
