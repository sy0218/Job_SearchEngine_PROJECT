#!/usr/bin/python3
import time, re, requests
from common.crawling_class import ChromeDriver, JobParser
from common.job_class import DataPreProcessor
from common.redis_hook import RedisHook
from common.kafka_hook import KafkaHook

from lxml import etree
from PIL import Image
from io import BytesIO

test_dict = {"domain":"jobplanet","href":"https://www.wanted.co.kr/wd/338837","company":"올릿","title":"마케팅 리더","msgid":"020d11cf3fce0e19060a3c3fffe4664c8360e62c246883a9621b705d3a78c95d"}

browser = ChromeDriver()
browser.get(test_dict['href'])
if "페이지를 찾을 수 없어요" in browser.driver.page_source:
    print(f"삭제된 공고: {test_dict['href']}")
browser.wait_css("section[class='JobContent_JobContent__Qb6DR']", 10)

# 사전셋업 필요
setup_list = ["//button[.//span[contains(text(), '상세 정보 더 보기')]]"]
browser.Jobplanet_Auto_Mation(setup_list, 30)

parser = JobParser(browser)
response = parser.get_response()

print(browser.title)

fields = {
    'pay': ['연봉', '보상금'],
    'location': ['근무지', '근무 장소', '근무지역'],
    'career': ['경력', '신입'],
    'education': ['학력'],
    'deadline': ['마감일'],
    'type': ['직급', '직책', '고용형태']
}
result = {}


for field, keywords in fields.items():
    result[field] = None
    for kw in keywords:
        xpath_query_list = [
            f"//span[contains(@class, 'JobHeader_JobHeader__Tools__Company__Info') and contains(text(), '{kw}')]/text()",
            f"//h2[contains(text(), '{kw}')]/following-sibling::span[contains(@class, 'wds')]/text()",
            f"//h2[contains(text(), '{kw}')]/following-sibling::*//span[contains(@class, 'wds')]/text()"
        ]

        for xpath_query in xpath_query_list:
            val = response.xpath(xpath_query).get()
            if val:
                result[field] = val.strip()
                break


print(result)

#result_test = response.xpath("//div[@class='sc-a34accef-0 cBEpAk']").get()
#parser = etree.HTMLParser()
#tree = etree.fromstring(result_test, parser)
#pretty_html = etree.tostring(tree, pretty_print=True, encoding='unicode')
#print(pretty_html)


#html = response.xpath("//div[@class='JobDescription_JobDescription__paragraph__wrapper__WPrKC']").getall()
#html = " ".join(html)

#parser = etree.HTMLParser()
#tree = etree.fromstring(html, parser)

#pretty_html = etree.tostring(tree, pretty_print=True, encoding='unicode')
# html 트리구조 보기
#print(pretty_html)
#print()

# 텍스트만 추출
#text_only = ''.join(tree.itertext())
# 한글, 영어, 숫자, 공백만 남기고 나머지 제거 (이모지, 특수문자 제거)
#clean_text = re.sub(r'[^가-힣a-zA-Z0-9\s%~/]', ' ', text_only)
# 연속 공백 정리
#clean_text = re.sub(r'\s+', ' ', clean_text).strip()
#print(clean_text)


# 이미지 마지막!
#img_tags = tree.xpath(".//img")
#for img in img_tags:
#    src = img.get("src")
#    try:
#        resp = requests.get(src, timeout=5)
#        img_bytes = resp.content # 바이너리 데이터
#        img_size_kb = len(img_bytes) / 1024

        # 이미지 크기 확인
#        img_file = Image.open(BytesIO(img_bytes))
#        width, height = img_file.size

#        if width <= 50 or height <= 50 or img_size_kb < 10:
#            continue
#        print(f"src: {src}, width: {width}, height: {height}, size: {img_size_kb:.2f}")
#        print(f"binary data: {img_bytes}")
#    except Exception as e:
#        print(f"src: {src}, error: {e}")

browser.quit()
