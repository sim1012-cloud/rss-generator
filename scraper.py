import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import datetime

def generate_rss():
    url = 'https://www.wenxuecity.com/news/'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    # 1. 获取网页内容
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 2. 初始化 RSS Feed
    fg = FeedGenerator()
    fg.title('文学城焦点新闻')
    fg.link(href=url, rel='alternate')
    fg.description('通过 GitHub Actions 自动抓取的文学城新闻 RSS')
    
    # 3. 提取新闻链接与标题 (针对文学城新闻列表的基础适配)
    # 寻找所有的 a 标签，筛选有效的新闻链接
    for item in soup.find_all('a'):
        link = item.get('href', '')
        title = item.text.strip()
        
        # 基础过滤：必须是新闻链接，且标题有实质内容
        if '/news/20' in link and title and len(title) > 4:
            if not link.startswith('http'):
                link = 'https://www.wenxuecity.com' + link
                
            fe = fg.add_entry()
            fe.title(title)
            fe.link(href=link)
            fe.id(link)
            # 时间强制设定为抓取时的 UTC 时间
            fe.pubDate(datetime.datetime.now(datetime.timezone.utc))
            
    # 4. 输出 XML 文件
    fg.rss_file('wenxuecity.xml')

if __name__ == "__main__":
    generate_rss()
