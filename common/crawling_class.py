#!/usr/bin/python3
from conf.config_log import setup_logger
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from scrapy.http import TextResponse
from w3lib.html import remove_tags

# 이미지 처리용
from lxml import etree
from PIL import Image
from io import BytesIO

import random, time, re, requests
logger = setup_logger(__name__)


class ChromeDriver:
    """
    Selenium ChromeDriver 래퍼 클래스
    - Headless Chrome 실행
    - User-Agent 랜덤 적용
    - 자동 스크롤 지원
    """

    def __init__(self):
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36"
        ]

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--incognito")
        options.add_argument("--blink-settings=imagesEnabled=false")
        options.add_argument("--disable-logging")
        options.add_argument(f"user-agent={random.choice(user_agents)}")
        options.add_argument("--window-size=1920,1080")

        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        self.driver = webdriver.Chrome(options=options)
        logger.info("ChromeDriver 초기화 완료")

    def wait_css(self, element, timeout):
        """
        CSS Selector 기준 엘리먼트 로딩 대기
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f"{element}:last-child"))
            )
        except TimeoutException:
            logger.error(f"CSS 로딩 타임아웃: {element}")
            raise

    def wait_xpath(self, element, timeout):
        """
        XPATH Selector 기준 엘리먼트 로딩 대기
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, element))
            )
        except TimeoutException:
            logger.error(f"XPATH 로딩 타임아웃: {element}")
            raise

    def click_xpath(self, element):
        self.driver.find_element(By.XPATH, element).click()
        logger.info(f"XPATH 클릭 성공: {element}")

    def Jobplanet_Auto_Mation(self, selectors, timeout):
        for select in selectors:
            self.wait_xpath(select, timeout)
            self.click_xpath(select)

    def autoscroll(self, element, timeout, sleep_sec, max_retry):
        """
        페이지 하단까지 자동 스크롤
        - height 변화 없을 경우 max_retry 후 중단
        """
        check_height = self.driver.execute_script(
            "return document.body.scrollHeight"
        )
        retry = 0

        logger.debug(f"[INIT] scrollHeight={check_height}")

        while True:
            time.sleep(sleep_sec)

            # 스크롤 다운
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )

            self.wait_css(element, timeout)

            new_height = self.driver.execute_script(
                "return document.body.scrollHeight"
            )

            logger.debug(f"[SCROLL] scrollHeight={new_height}")

            if new_height == check_height:
                retry += 1
                logger.debug(
                    f"[RETRY] height unchanged ({retry}/{max_retry})"
                )

                if retry == max_retry:
                    logger.info("스크롤 종료 (max_retry 도달)")
                    break
            else:
                check_height = new_height

    def __getattr__(self, name):
        """
        webdriver 메서드 위임
        """
        return getattr(self.driver, name)


class JobParser:
    """
    Selenium 페이지 소스를 Scrapy TextResponse로 변환 후
    채용 공고 헤더 데이터 추출
    """

    def __init__(self, browser):
        self.browser = browser
        self.response = None

    def get_response(self):
        """
        현재 페이지 HTML → Scrapy TextResponse 변환
        """
        self.response = TextResponse(
            url=self.browser.current_url,
            body=self.browser.page_source,
            encoding="utf-8"
        )
        logger.debug("Scrapy TextResponse 생성 완료")
        return self.response

    def get_job(
        self,
        domain,
        job_html,
        href_path,
        company_path,
        title_path
    ):
        """
        단일 채용 공고 HTML에서 데이터 추출
        return: {domain, href, company, title}
        """
        href = self.response.urljoin(
            job_html.xpath(href_path).get() or ""
        ).strip()
        company = (job_html.xpath(company_path).get() or "").strip()
        title = (job_html.xpath(title_path).get() or "").strip()

        if not (href and company and title):
            logger.warning(job_html.get())
            raise ValueError(f"데이터 누락 발생..! (href: {href}, company: {company}, title: {title})")
        job_data = {
            "domain": domain,
            "href": href,
            "company": company,
            "title": title
        }

        return job_data

    def _clean_text_banner(self, text):
        # 줄바꿈 → 쉼표
        text = text.replace('\n', ',')
        # 특수문자 제거 (쉼표, 한글, 영어, 숫자, 공백은 유지)
        text = re.sub(r'[^가-힣a-zA-Z0-9,\s~.]', ' ', text)
        # 연속 공백/쉼표 정리
        text = re.sub(r'\s+', ' ', text)        # 연속 공백 → 1개 공백
        text = re.sub(r'\s*,\s*', ',', text)    # 쉼표 주변 공백 제거
        text = text.strip()
        return text

    def _clean_text_body(self, text):
        text = re.sub(r'[^가-힣a-zA-Z0-9\s/]+', '', text) # 특수문자 제거
        text = re.sub(r'\s+', ' ', text).strip()  # 연속 공백 제거
        return text

    def get_banner(self, xpaths, domain):
        """
        banner xpath 기반으로 pay/location/career/education/deadline/type 추출
        xpaths: {'banner': "xpath1|xpath2"}
        return: dict
        """
        banner = {}
        fields = {
            'pay': ['연봉', '보상금'],
            'location': ['근무지', '근무 장소'],
            'career': ['경력'],
            'education': ['학력'],
            'deadline': ['마감일'],
            'type': ['직급', '직책']
        }

        if domain == "remember":
            for field, keywords in fields.items():
                banner[field] = None
                for kw in keywords:
                    for xp in xpaths:
                        val = self.response.xpath(xp.format(kw=kw)).get()
                        if val:
                            banner[field] = self._clean_text_banner(val)
                            break
                    if banner[field]:
                        break
        return banner

    def get_body(self, xpath_body):
        """
        페이지 HTML에서 body 텍스트만 추출 후 정리
        - 특수문자 제거
        - 연속 공백 정리
        """
        html = self.response.xpath(xpath_body).get()
        text_only = remove_tags(html)
        text_only = self._clean_text_body(text_only)
        return text_only

    def get_images(self, xpath_body, page_url, min_width, min_height, min_size_kb):
        """
        HTML에서 이미지 src 리스트 추출
        - etree 사용, XPath로 img 태그 선택
        - 크기/용량 필터링 가능
        """
        img_lst = []
        html = self.response.xpath(xpath_body).get()
        tree = etree.HTML(html)

        for img in tree.xpath(".//img"):
            src = img.get("src")
            if not src:
                logger.info(f"img src 없음 | page: {page_url}")
                continue

            try:
                resp = requests.get(src, timeout=10)
                img_bytes = resp.content
                img_size_kb = len(img_bytes) / 1024

                if img_size_kb < min_size_kb:
                    logger.info(f"이미지 용량 작음 ({img_size_kb:.2f}KB) | page: {page_url}")
                    continue

                with Image.open(BytesIO(img_bytes)) as im:
                    if im.width < min_width or im.height < min_height:
                        logger.info(f"이미지 너무 작음 ({im.width}x{im.height}) | page: {page_url}")
                        continue
                img_lst.append((img_bytes, int(img_size_kb)))

            except Exception as e:
                logger.error(f"이미지 처리 실패 | page: {page_url} | error: {e}")
                continue

        return img_lst
