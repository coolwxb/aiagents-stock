import asyncio
import aiohttp
import datetime
from typing import List, Dict


class ThsSpider:
    """同花顺新闻爬虫"""
    
    def __init__(self):
        self.headers = {
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Pragma": "no-cache",
            "Referer": "https://news.10jqka.com.cn/realtimenews.html",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
        }
        self.url = "https://news.10jqka.com.cn/tapp/news/push/stock/"
        self.params = {
            "page": "1",
            "tag": "",
            "track": "website",
            "pagesize": "100"
        }

    async def fetch_news(self) -> List[Dict]:
        """获取同花顺新闻列表"""
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(self.url, params=self.params) as response:
                    if response.status != 200:
                        print(f"请求失败，状态码: {response.status}")
                        return []
                    
                    res = await response.json()
                    news_list = []

                    if 'data' in res and 'list' in res['data']:
                        for item in res['data']['list']:
                            try:
                                # 解析时间戳
                                timestamp = int(item.get('ctime', 0))
                                ctime = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                                
                                # 获取标签ID（如果存在）
                                tag_id = ""
                                if item.get('tags') and len(item['tags']) > 0:
                                    tag_id = item['tags'][0].get('id', '')
                                
                                news_item = {
                                    'title': item.get('title', ''),
                                    'content': item.get('digest', ''),
                                    'datetime': ctime,
                                    'color': tag_id,
                                    'url': item.get('url', '')
                                }
                                news_list.append(news_item)
                            except Exception as e:
                                print(f"解析新闻项失败: {e}")
                                continue

                    return news_list

        except aiohttp.ClientError as e:
            print(f"网络请求失败: {str(e)}")
            return []
        except Exception as e:
            print(f"同花顺新闻获取失败: {str(e)}")
            return []


async def test():
    spider = ThsSpider()
    news = await spider.fetch_news()
    print(f"获取到 {len(news)} 条新闻")
    print("-" * 50)
    for item in news[:5]:  # 打印前5条
        print(f"时间: {item['datetime']}")
        print(f"标题: {item['title']}")
        print(f"内容: {item['content'][:100]}..." if len(item['content']) > 100 else f"内容: {item['content']}")
        print("-" * 50)


if __name__ == "__main__":
    asyncio.run(test())
