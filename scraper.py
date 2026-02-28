import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import datetime
import time
import re

def get_article_details(url, headers):
    try:
        time.sleep(1.5)
        req_headers = headers.copy()
        req_headers['Referer'] = 'https://www.wenxuecity.com/news/'
        
        response = requests.get(url, headers=req_headers, timeout=15)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            return "<p>抓取被服务器拒绝</p>"
            
        soup = BeautifulSoup(response.text, 'html.parser')
        content_div = soup.find('div', id='articleContent') or soup.find('div', id='article') or soup.find('div', class_='news-content') or soup.find('body')
        
        img_html = ""
        summary_text = ""
        
        if content_div:
            for hidden in content_div(["script", "style", "iframe"]):
                hidden.extract()
                
            first_img = content_div.find('img')
            if first_img and first_img.get('src'):
                img_src = first_img.get('src')
                if not img_src.startswith('http'):
                    img_src = 'https://www.wenxuecity.com' + img_src
                # 规范化图片尺寸与留白，兼容卡片视图
                img_html = f'<div style="margin-bottom: 15px;"><img src="{img_src}" style="max-width: 100%; height: auto; border-radius: 6px; display: block;" /></div>'
                
            paragraphs = content_div.find_all('p')
            if paragraphs:
                raw_text = " ".join([p.get_text(strip=True) for p in paragraphs])
            else:
                raw_text = content_div.get_text(strip=True)
                
            raw_text = re.sub(r'\s+', ' ', raw_text).strip()
            
            if len(raw_text) > 200:
                summary_text = raw_text[:200] + "..."
            elif len(raw_text) > 0:
                summary_text = raw_text
                
        if not summary_text:
            summary_text = "未能提取到正文。"
            
        # 直接输出合并好的单一 HTML，不再做拆分
        return f'{img_html}<p style="font-size: 14px; color: #444; line-height: 1.6; margin: 0;">{summary_text}</p>'
        
    except Exception as e:
        return f"<p>抓取失败: {e}</p>"


def generate_rss():
    base_url = 'https://www.wenxuecity.com/news/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    response = requests.get(base_url, headers=headers)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    fg = FeedGenerator()
    fg.title('文学城焦点新闻 (高规格卡片流)')
    fg.link(href=base_url, rel='alternate')
    fg.description('通过 GitHub Actions 强制穿透 Inoreader 缓存')
    
    article_links = []
    for item in soup.find_all('a'):
        link = item.get('href', '')
        title = item.text.strip()
        if '/news/20' in link and title and len(title) > 4:
            if not link.startswith('http'):
                link = 'https://www.wenxuecity.com' + link
            if not any(entry['link'] == link for entry in article_links):
                article_links.append({'title': title, 'link': link})
                
    max_items = 20
    processed_count = 0
    
    # 获取本次运行的全局时间戳，用于“污染”链接
    run_timestamp = str(int(time.time()))
    
    for article in article_links:
        if processed_count >= max_items:
            break
            
        print(f"[{processed_count+1}/{max_items}] 正在处理: {article['title']}")
        
        # 提取合并好的富文本
        html_content = get_article_details(article['link'], headers)
        
        fe = fg.add_entry()
        fe.title(article['title'])
        
        # 核心改动：在原网址后加上无意义的时间戳参数 ?v=xxx
        # 这对原网页打开毫无影响，但会让 Inoreader 误以为这是全网首发的全新文章
        unique_url = article['link'] + "?v=" + run_timestamp
        
        fe.link(href=unique_url)
        fe.id(unique_url)
        
        # 将图文 HTML 直接塞入 description
        fe.description(html_content)
        
        fe.pubDate(datetime.datetime.now(datetime.timezone.utc))
        processed_count += 1
            
    fg.rss_file('wenxuecity.xml')
    print("====== RSS 源生成完毕，缓存已击穿 ======")

if __name__ == "__main__":
    generate_rss()
