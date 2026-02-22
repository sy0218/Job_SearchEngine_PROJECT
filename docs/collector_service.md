# 📡 collector.service (Job Header Scraper)
> 구인구직 사이트 채용 정보를 자동으로 수집하는 **백그라운드 서비스**입니다.

- **systemd + Docker 기반 서비스**
- **Selenium + Scrapy** 기반 웹 크롤러
- **Redis**로 중복 데이터 필터링
- **Kafka Avro**로 실시간 데이터 전송
- 환경 설정 파일 기반 **도메인 확장 구조**

---
<br>

## 🔄 Collector Pipline
![Pipline](https://github.com/user-attachments/assets/4d2b53a0-6c41-471c-9fd3-10fd28fb7ebb)
---
<br>

## 📂 주요 파일 구조
| 파일명 | 설명 |
|--------|------|
| `collector.service` | systemd 유닛 파일 (Docker 내부 서비스 실행) |
| `collector.sh` | 환경 변수 로드 및 서비스 시작/중지 스크립트 |
| **`collector.py` (메인)** | **도메인별 크롤링 실행 및 Stop 감지** |
| `job.conf` | 전체 서비스 환경 변수 설정 |
| `collector.properties` | 도메인/URL/XPath/옵션 설정 |
| `config_log.py` | 날짜별 로그 파일 생성 |
| `common/job_class.py` | 환경 변수 로더, StopChecker, 데이터 전처리 |
| `common/crawling_class.py` | Selenium ChromeDriver + JobParser |
| `common/redis_hook.py` | Redis 연결 클래스 |
| `common/kafka_hook.py` | Kafka Producer/Consumer 클래스 |

---
<br>

## ▶️ 서비스 동작 흐름
```plaintext
systemd (collector.service)
   │
   └─ docker exec → collector.sh start
          │
          └─ collector.py (_main)
                 │
                 ├─ 환경 변수 및 설정 로드
                 ├─ Redis 연결 (중복 체크)
                 ├─ Kafka Avro Producer 연결
                 ├─ ChromeDriver 시작
                 │
                 ├─ 도메인 & 직무 반복 수집
                 │    ├─ URL 접속
                 │    ├─ 자동 설정/페이지/스크롤
                 │    ├─ HTML → Scrapy 변환
                 │    ├─ 채용 데이터 파싱
                 │    ├─ Redis 중복 체크
                 │    └─ Kafka 전송
                 │
                 └─ Stop 파일 감지 시 안전 종료
```

---
<br>

## 🌟 주요 특징
- properties 기반 **도메인/직무 동적 크롤링**
- **page/scroll 크롤링 방식 지원**
- Redis Set 기반 중복 제거
- Kafka Avro 실시간 메시지 전송
- Stop 플래그 기반 shutdown

---
<br>

## 📋 환경 변수 (job.conf)
```bash
export PYTHONPATH=/work/job_project
export JOB_LIB=/work/jsy/job_project/lib

# 컬렉터 (service)
export COLLECTOR_CONFIG_PATH=/work/job_project/collector/conf/collector.properties
export COLLECTOR_WORK_DIR=/work/job_project/collector
export COLLECTOR_STOP_DIR=/work/job_project/collector/control
export COLLECTOR_STOP_FILE=collector.stop
export COLLECTOR_LOG_FILE=/work/job_project/logs/collector/collector

# 컨슈머 (service)
export CONSUMER_CONFIG_PATH=/work/job_project/consumer/conf/consumer.properties
export CONSUMER_WORK_DIR=/work/job_project/consumer
export CONSUMER_STOP_DIR=/work/job_project/consumer/control
export CONSUMER_STOP_FILE=consumer.stop
export CONSUMER_LOG_FILE=/work/job_project/logs/consumer/consumer

# 하둡 업로드 (service)
export HD_UPLOAD_CONFIG_PATH=/work/jsy/job_project/hadoop_upload/conf/hadoop_upload.properties
export HD_UPLOAD_WORK_DIR=/work/jsy/job_project/hadoop_upload
export HD_UPLOAD_STOP_DIR=/work/jsy/job_project/hadoop_upload/control
export HD_UPLOAD_STOP_FILE=hadoop_upload.stop
export HD_UPLOAD_LOG_DIR=/work/jsy/job_project/logs/hadoop_upload

# 하둡 이벤트 (service)
export HD_EVENT_CONFIG_PATH=/work/jsy/job_project/hadoop_event/conf/hadoop_event.properties
export HD_EVENT_WORK_DIR=/work/jsy/job_project/hadoop_event
export HD_EVENT_LOG_DIR=/work/jsy/job_project/logs/hadoop_event

# ocr (service)
export OCR_CONFIG_PATH=/work/job_project/ocr/conf/ocr.properties
export OCR_WORK_DIR=/work/job_project/ocr
export OCR_STOP_DIR=/work/job_project/ocr/control
export OCR_STOP_FILE=ocr.stop
export OCR_LOG_FILE=/work/job_project/logs/ocr/ocr

# 웨어하우스 (service)
export WAREHOUSE_CONFIG_PATH=/work/job_project/warehouse/conf/warehouse.properties
export WAREHOUSE_WORK_DIR=/work/job_project/warehouse
export WAREHOUSE_STOP_DIR=/work/job_project/warehouse/control
export WAREHOUSE_STOP_FILE=warehouse.stop
export WAREHOUSE_LOG_FILE=/work/job_project/logs/warehouse/warehouse

# 엘라스틱서치 업로드 (service)
export ES_UPLOAD_CONFIG_PATH=/work/job_project/es_upload/conf/es_upload.properties
export ES_UPLOAD_WORK_DIR=/work/job_project/es_upload
export ES_UPLOAD_STOP_DIR=/work/job_project/es_upload/control
export ES_UPLOAD_STOP_FILE=es_upload.stop
export ES_UPLOAD_LOG_FILE=/work/job_project/logs/es_upload/es_upload

# redis (app)
export REDIS_HOST=192.168.122.59
export REDIS_PORT=6379
export REDIS_DB_JOB=0
export REDIS_DB_IMG=1
export REDIS_PASSWORD=1234
export REDIS_JOBHEAD_KEY=job_set

# kafka (app)
export KAFKA_HOST=192.168.122.60:9092,192.168.122.61:9092,192.56.122.62:9092
export SCHEMA_REGISTRY=http://192.168.122.59:8081
export JOB_TOPIC=job_header_topic
export JOB_GROUP_ID=job-group
export OCR_TOPIC=ocr_img
export OCR_GROUP_ID=ocr-group

# postgresql (app)
export POSTGRESQL_HOST=192.168.122.59
export POSTGRESQL_PORT=5432
export POSTGRESQL_DB=job_pro
export POSTGRESQL_USER=sjj
export POSTGRESQL_PASSWORD=1234

# hadoop (app)
export HADOOP_FS_NAME=job-cluster
export HADOOP_USER=root

# elasticsearch (app)
export ES_HOST=http://192.168.122.63:9200,http://192.168.122.64:9200,http://192.168.122.65:9200
export ES_JOB_INDEX=job_postings_v1

# nfs
export NFS_DATA=/nfs/job_data
export NFS_IMG=/nfs/img
```

---
<br>

## 📋 설정 파일 (collector.properties)
```bash
[domain]
catagory=saramin,wanted,jobplanet,remember

[job_catagory_count]
count=2

[url_number]
url1=marketing
url2=it

[url]
saramin.url.it=https://www.saramin.co.kr/zf_user/jobs/list/job-category?cat_mcls=2&panel_type=&search_optional_item=n&search_done=y&panel_count=y&preview=y&page={page}&sort=RD&page_count=100
remember.url.it=https://career.rememberapp.co.kr/job/postings?search=%7B%22organizationType%22%3A%22without_headhunter%22%2C%22jobCategoryNames%22%3A%5B%7B%22level1%22%3A%22SW%EA%B0%9C%EB%B0%9C%22%7D%2C%7B%22level1%22%3A%22AI%C2%B7%EB%8D%B0%EC%9D%B4%ED%84%B0%22%7D%5D%7D
jobplanet.url.it=https://www.jobplanet.co.kr/job
wanted.url.it=https://www.wanted.co.kr/wdlist/518?country=kr&job_sort=job.latest_order&years=-1&locations=all

saramin.url.marketing=https://www.saramin.co.kr/zf_user/jobs/list/job-category?cat_mcls=14&panel_type=&search_optional_item=n&search_done=y&panel_count=y&preview=y&page={page}&page_count=100
remember.url.marketing=https://career.rememberapp.co.kr/job/postings?search=%7B%22organizationType%22%3A%22without_headhunter%22%2C%22jobCategoryNames%22%3A%5B%7B%22level1%22%3A%22%EB%A7%88%EC%BC%80%ED%8C%85%C2%B7%EA%B4%91%EA%B3%A0%22%7D%5D%7D
jobplanet.url.marketing=https://www.jobplanet.co.kr/job
wanted.url.marketing=https://www.wanted.co.kr/wdlist/523?country=kr&job_sort=job.popularity_order&years=-1&locations=all

[option]
saramin.setup_flag=n
saramin.crawling_type=page

remember.setup_flag=n
remember.crawling_type=scroll

jobplanet.setup_flag=y
jobplanet.crawling_type=scroll

wanted.setup_flag=n
wanted.crawling_type=scroll

[xpath]
saramin.response=//div[contains(@id, "rec-") and @class="list_item"]
saramin.href=concat(substring-before(.//div[@class="job_tit"]/a/@href, "/relay/"), "/", substring-after(.//div[@class="job_tit"]/a/@href, "/relay/"))
saramin.company=.//div[@class="col company_nm"]/a/text() | .//div[@class="col company_nm"]/span/text()
saramin.title=.//div[@class="job_tit"]/a/@title
saramin.wait=div.list_item[id^="rec-"]

remember.response=//li[@class="sc-364cfa5d-0 hzhbKf"]//a
remember.href=substring-before(./@href, "?")
remember.company=.//p/text()
remember.title=.//h4/text() | .//h6/text()
remember.wait=li[class="sc-364cfa5d-0 hzhbKf"

jobplanet.response=//div[@class="overflow-hidden medium"]/a
jobplanet.href=./@href
jobplanet.company=.//div[contains(@class, "medium")]/em/text()
jobplanet.title=.//h4/text()
jobplanet.wait=div[class="overflow-hidden medium"]

wanted.response=//div[@data-cy="job-card"]/a
wanted.href=./@href
wanted.company=.//span[contains(@class, "company")]/text()
wanted.title=.//span[contains(@class, "position")]/text()
wanted.wait=div[data-cy="job-card"]

[auto_setup]
jobplanet.it=//a[contains(@class, "jf_b2") and contains(text(), "직종")]        //button[contains(@class, "jf_b1") and contains(text(), "개발")]        //span[contains(@class, "jf_b1") and contains(text(), "개발 전체")]    //button[contains(@class, "jf_b1") and text()="데이터"] //span[contains(@class, "jf_b1") and contains(text(), "데이터 전체")]   //button[contains(@class, "jf_h9") and text()="적용"]
jobplanet.marketing=//a[contains(@class, "jf_b2") and contains(text(), "직종")] //button[contains(@class, "jf_b1") and contains(text(), "마케팅/시장조사")]     //span[contains(@class, "jf_b1") and contains(text(), "마케팅/시장조사 전체")]  //button[contains(@class, "jf_h9") and text()="적용"]

[schema]
job_header=/work/job_project/schema/kafka/job_header.avsc
```

---
<br>

## ▶️ 서비스 실행
```bash
# 시작
sudo systemctl start collector.service

# 중지
sudo systemctl stop collector.service

# 상태 확인
sudo systemctl status collector.service
```

---
<br>

## 📜 로그
- 로그 파일 위치:
`/work/job_project/logs/collector/collector_YYYYMMDD.log`
- 예시:
`/work/job_project/logs/collector/collector_20260205.log`

---
<br>

## ✅ 주의 사항
- Stop 파일 생성 시 Collector가 안전하게 종료됨
- ChromeDriver는 Headless + 랜덤 User-Agent 사용
- Kafka Schema Registry 등록 필수
- Redis Set으로 중복 데이터 필터링
- XPath 변경 시 properties 파일 수정 필요
---
