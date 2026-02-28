import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import datetime
import time

def get_article_details(url, headers):
    """进入文章内页抓取首图和正文前200字"""
    try:
        time.sleep(1) # 强制延时 1 秒，极其重要！防止被文学城封禁 GitHub IP
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 寻找正文容器 (兼容常见的容器 id 或 class)
        content_div = soup.find('div', id='articleContent') or soup.find('div', class_='news-content') or soup.find('div', id='postbody')
        
        img_html = ""
        summary_text = "暂无正文摘要"
        
        if content_div:
            # 1. 提取首图
            first_img = content_div.find('img')
            if first_img and first_img.get('src'):
                img_src = first_img.get('src')
                if not img_src.startswith('http'):
                    img_src = 'https://www.wenxuecity.com' + img_src
                # 将图片包装为 HTML 格式
                img_html = f'<div style="margin-bottom: 10px;"><img src="{img_src}" style="max-width: 100%; border-radius: 8px;"></div>'
                
            # 2. 提取正文并截取前 200 字
            paragraphs = content_div.find_all('p')
            raw_text = " ".join([p.text.strip() for p in paragraphs if p.text.strip()])
            if not raw_text:
                # 如果没有 p 标签，直接取 div 的文字
                raw_text = content_div.text.strip()
                
            # 清理换行符并截断
            raw_text = " ".join(raw_text.split())
            if len(raw_text) > 200:
                summary_text = raw_text[:200] + "..."
            elif len(raw_text) > 0:
                summary_text = raw_text
                
        return img_html + f'<p style="font-size: 14px; color: #333; line-height: 1.6;">{summary_text}</p>'
    except Exception as e:
        print(f"Error fetching details for {url}: {e}")
        return "<p>无法抓取详情内容或请求超时。</p>"

def generate_rss():
    base_url = 'https://www.wenxuecity.com/news/'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    response = requests.get(base_url, headers=headers)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    fg = FeedGenerator()
    fg.title('文学城焦点新闻 (图文版)')
    fg.link(href=base_url, rel='alternate')
    fg.description('通过 GitHub Actions 自动深度抓取的文学城图文 RSS')
    
    # 获取有效的新闻链接列表
    article_links = []
    for item in soup.find_all('a'):
        link = item.get('href', '')
        title = item.text.strip()
        if '/news/20' in link and title and len(title) > 4:
            if not link.startswith('http'):
                link = 'https://www.wenxuecity.com' + link
            # 查重，避免同一新闻不同入口重复抓取
            if not any(entry['link'] == link for entry in article_links):
                article_links.append({'title': title, 'link': link})
                
    # 核心限制：仅深度抓取前 20 条，控制预算与风险
    max_items = 20
    processed_count = 0
    
    for article in article_links:
        if processed_count >= max_items:
            break
            
        print(f"[{processed_count+1}/{max_items}] Fetching: {article['title']}")
        
        # 调用深度抓取函数
        description_html = get_article_details(article['link'], headers)
        
        fe = fg.add_entry()
        fe.title(article['title'])
        fe.link(href=article['link'])
        fe.id(article['link'])
        # 写入包含 HTML 标签的描述内容
        fe.description(description_html)
        fe.pubDate(datetime.datetime.now(datetime.timezone.utc))
        
        processed_count += 1
            
    fg.rss_file('wenxuecity.xml')
    print("RSS Feed Generated Successfully.")

if __name__ == "__main__":
    generate_rss()
