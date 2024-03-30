import time
from typing import List

from tqdm import tqdm
from NewsScraper.models.news import NewsContent
from NewsScraper.config.scraper_config import ScraperConfig
from NewsScraper.scraper.main_scraper import MainScraper
from NewsScraper.scraper_data.scraper_data import ScraperData
from NewsScraper.scraper_progress.scraper_progress import ScraperProgress
from NewsScraper.scraper_url.scraper_url import ScraperUrl
from NewsScraper.bs4_engine.open_connection import open_bs4_connection


class CNNScraper(MainScraper):
    def __init__(self, 
                 config: ScraperConfig, 
                 progress: ScraperProgress, 
                 news_url: ScraperUrl,
                 dataset: ScraperData):
        super().__init__(config, progress, news_url, dataset)

    def read_urls(self) -> List[str]:
        all_links = []
        for i in tqdm(range(self.config.num_of_page), desc='[ACTIVITY] Processing News Pages:'):
            trial = 0
            while True:
                try:
                    id = 1+i
                    url = f'{self.config.base_url}{id}'
                    page_links = self.read_urls_in_news_list(url)
                    all_links.extend(page_links)
                    break
                except Exception as e:
                    trial += 1
                    print('[ERR] Something wrong!!', e)
                    if trial > 5:
                        is_cancel = input('Skip? (y/n) ')
                        if is_cancel.lower() == 'y':
                            break
                        
                    print('[ERR] Retrying in 5 seconds...')
                    time.sleep(5)

        self.news_url.save_url_temp(all_links)
        return all_links
    
    def read_urls_in_news_list(self, page_url: str) -> List[str]:
        soup = open_bs4_connection(page_url)
        
        news_container = soup.find("div", {"class": "flex flex-col gap-5"})
        news_boxes = news_container.find_all("article", {})

        links = []
        for news in news_boxes:
            link_a = news.find('a', href=True)
            link = link_a['href']
            links.append(link)
        
        return links

    def scrap_news_content(self, url: str) -> NewsContent:
        soup = open_bs4_connection(url)
        
        news_title = soup.find("h1", {"class": "mb-2 text-[28px] leading-9 text-cnn_black"})
        news_title = news_title.text.strip() if news_title is not None else ''

        news_timestamp = soup.find("div", {"class": "text-cnn_grey text-sm mb-4"})
        news_timestamp = news_timestamp.text.strip() if news_timestamp is not None else ''

        news_full_text = soup.find("div", {"class": "detail-text text-cnn_black text-sm grow min-w-0"})
        if not news_full_text:
            news_full_text = soup.find("div", {"class": "detail_text"})
        news_full_text = news_full_text.text.strip() if news_full_text is not None else ''
        
        news_tag_div = soup.find("div", {"class": "flex flex-wrap gap-3"})
        if news_tag_div:
            news_tags = news_tag_div.find_all("a")
            news_tags = [tag.text.strip() if tag is not None else '' for tag in news_tags]
            news_tags = ';'.join(news_tags)
        else:
            news_tags = ''
        
        news_author = soup.find("div", {"class": "text-cnn_black_light3 text-sm mb-2.5"})
        news_author = news_author.text.strip() if news_author is not None else ''

        news = NewsContent(
            title=news_title,
            timestamp=news_timestamp,
            full_text=news_full_text,
            tags=news_tags,
            url=url,
            author=news_author,
        )
        return news
