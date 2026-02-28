import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import datetime
import time
import re

def get_article_details(url, headers):
    """进入文章内页深度抓取首图和正文摘要"""
    try:
        time.sleep(1.5) # 强制延时，避免被防火墙阻截
        # 增加 Referer 模拟真实点击跳转
        req_headers = headers.copy()
        req_headers['Referer'] = 'https://www.wenxuecity.com/news/'
        
        response = requests.get(url, headers=req_headers, timeout=15)
        response.encoding = 'utf-8'
        
        # 验证是否遭遇反爬拦截 (如 Cloudflare 验证码页面)
        if response.status_code != 200:
            print(f"  -> [拦截] 状态码: {response.status_code}")
            return "抓取被服务器拒绝", f"<p>抓取被服务器拒绝 (HTTP {response.status_code})</p>"
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 多层级寻找正文容器 (覆盖文学城常见的多种排版)
        content_div = soup.find('div', id='articleContent') or soup.find('div', id='article') or soup.find('div', class_='news-content')
        
        if not content_div:
            # 极限兜底：直接抓取主体
            content_div = soup.find('body')
            
        img_html = ""
        summary_text = ""
        has_img = False
        
        if content_div:
            # 1. 清理干扰标签 (广告、脚本、样式表)
            for hidden in content_div(["script", "style", "iframe"]):
                hidden.extract()
                
            # 2. 提取首图
            first_img = content_div.find('img')
            if first_img and first_img.get('src'):
                img_src = first_img.get('src')
                if not img_src.startswith('http'):
                    img_src = 'https://www.wenxuecity.com' + img_src
                # 规范化图片尺寸比例与留白
                img_html = f'<div style="margin-bottom: 20px;"><img src="{img_src}" style="max-width: 100%; height: auto; border-radius: 4px;" /></div>'
                has_img = True
                
            # 3. 提取文字
            paragraphs = content_div.find_all('p')
            if paragraphs:
                raw_text = " ".join([p.get_text(strip=True) for p in paragraphs])
            else:
                raw_text = content_div.get_text(strip=True)
                
            # 清洗多余的空格与换行
            raw_text = re.sub(r'\s+', ' ', raw_text).strip()
            
            # 截取 200 字
            if len(raw_text) > 200:
                summary_text = raw_text[:200] + "..."
            elif len(raw_text) > 0:
                summary_text = raw_text
                
        if not summary_text:
            summary_text = "未能提取到正文，可能页面仅包含视频或遭到验证码拦截。"
            
        print(f"  -> [提取成功] 包含图片: {has_img}, 摘要长度: {len(summary_text)}")
        
        # 组装富文本格式
        full_html_content = f'{img_html}<p style="font-size: 15px; color: #333333; line-height: 1.6;">{summary_text}</p>'
        
        return summary_text, full_html_content
        
    except Exception as e:
        print(f"  -> [报错] 请求超时或解析失败: {e}")
        return "抓取超时或出错", "<p>抓取超时或出错，请点击原文查看。</p>"


def generate_rss():
    base_url = 'https://www.wenxuecity.com/news/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    response = requests.get(base_url, headers=headers)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    fg = FeedGenerator()
    fg.title('文学城焦点新闻 (高规格图文版)')
    fg.link(href=base_url, rel='alternate')
    fg.description('通过 GitHub Actions 自动化深度抓取')
    
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
    
    for article in article_links:
        if processed_count >= max_items:
            break
            
        print(f"[{processed_count+1}/{max_items}] 正在处理: {article['title']}")
        
        # 获取纯文本与富文本双格式
        plain_summary, html_content = get_article_details(article['link'], headers)
        
        fe = fg.add_entry()
        fe.title(article['title'])
        fe.link(href=article['link'])
        fe.id(article['link'])
        
        # 双轨输出，兼容所有阅读器
        fe.description(plain_summary) 
        fe.content(content=html_content, type='html') 
        
        fe.pubDate(datetime.datetime.now(datetime.timezone.utc))
        processed_count += 1
            
    fg.rss_file('wenxuecity.xml')
    print("====== RSS 源生成完毕 ======")

if __name__ == "__main__":
    generate_rss()
