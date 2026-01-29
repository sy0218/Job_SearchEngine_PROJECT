# 📡 collector.service (Job Header Scraper)
> 구인구직 사이트 채용 정보를 자동으로 수집하는 **백그라운드 서비스**입니다.

- **systemd 서비스**로 자동 실행 및 관리
- **Selenium + Scrapy** 기반 웹 크롤러
- **Redis**로 중복 데이터 필터링
- **Kafka**로 실시간 데이터 전송
- 환경 설정 파일로 도메인별 수집 관리

---
<br>


## 📂 주요 파일 구조
| 파일명 | 설명 |
|--------|------|
| `collector.service` | systemd 유닛 파일 (서비스 관리) |
| `collector.sh` | 환경 변수 로드 및 서비스 시작/중지 스크립트 |
| **`collector.py` (메인)** | 도메인별 잡 실행 및 종료 감지 |
| `job.conf` | 환경 변수 설정 파일 |
| `collector.properties` | 도메인/URL/XPath/스키마 설정 |
| `config_log.py` | 로그 설정 (날짜별 파일 생성) |
| `common/hook_class.py` | Kafka / Redis / PostgreSQL Hook |
| `common/crawling_class.py` | Selenium 래퍼, 채용 데이터 파서 |
| `common/job_class.py` | 환경 변수, StopChecker, 데이터 전처리 클래스 |

---
<br>


## ▶️ 서비스 동작 흐름
```plaintext
systemd (collector.service)
   │
   └─ collector.sh start
          │
          └─ collector.py (_main)
                 │
                 ├─ 환경 변수 및 설정 로드
                 ├─ Redis 연결 (중복 체크)
                 ├─ Kafka Avro Producer 연결
                 ├─ ChromeDriver 브라우저 시작
                 │
                 ├─ 도메인 & 잡별 반복 수집
                 │    ├─ Job URL 접속
                 │    ├─ 페이지 대기 & 자동 스크롤
                 │    ├─ HTML → Scrapy TextResponse 변환
                 │    ├─ 채용 데이터 추출 (domain, href, company, title)
                 │    ├─ Redis 중복 체크
                 │    └─ Kafka 전송
                 │
                 └─ Stop 파일 감지 시 안전 종료
```

---
<br>


## 🌟 주요 특징
- 설정 기반 **도메인/잡 순차 실행**
- Redis로 중복 데이터 제거
- Kafka에 실시간 데이터 전송
- Stop 플래그 감지 시 안전하게 종료

---
<br>


## 📋 환경 변수 (job.conf)
```bash
export PYTHONPATH=/work/job_project

# Collector
export COLLECTOR_CONFIG_PATH=/work/job_project/collector/conf/collector.properties
export COLLECTOR_WORK_DIR=/work/job_project/collector
export COLLECTOR_STOP_DIR=/work/job_project/collector/control
export COLLECTOR_STOP_FILE=collector.stop
export COLLECTOR_LOG_FILE=/work/job_project/logs/collector

# Redis
export REDIS_HOST=192.168.122.59
export REDIS_PORT=6379
export REDIS_DB=0
export REDIS_PASSWORD=1234
export REDIS_JOBHEAD_KEY=job_set

# Kafka
export KAFKA_HOST=192.168.122.60:9092,192.168.122.61:9092,192.56.122.62:9092
export SCHEMA_REGISTRY=http://192.168.122.59:8081
export JOB_TOPIC=job_header_topic

# PostgreSQL
export POSTGRESQL_HOST=192.168.122.59
export POSTGRESQL_PORT=5432
export POSTGRESQL_DB=job_pro
export POSTGRESQL_USER=sjj
export POSTGRESQL_PASSWORD=1234
```

---
<br>


## 📋 설정 파일 (collector.properties)
```ini
[domain]
catagory=remember

[job_catagory_count]
count=1

[url_number]
url1=it

[url]
saramin.url.it=https://www.saramin.co.kr/zf_user/jobs/list/job-category?cat_mcls=2&...
remember.url.it=https://career.rememberapp.co.kr/job/postings?search=%7B%22organizationType%22...

[xpath]
saramin.response.it=//div[@class='list_body']/div[@class='list_item' or @class='list_item effect']
saramin.href.it=.//a[@class='str_tit ']/@href
saramin.company.it=.//a[@class='str_tit']/text()
saramin.title.it=.//a[@class='str_tit ']/@title

remember.response.it=//li[@class="sc-364cfa5d-0 hzhbKf"]//a
remember.href.it=substring-before(./@href, "?")
remember.company.it=.//p/text()
remember.title.it=.//h4/text() | .//h6/text()
remember.wait.it=a[href^="/job/posting/"]

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
- 로그 파일 위치: `$COLLECTOR_LOG_FILE_YYYYMMDD.log`
- 예시: `/work/job_project/logs/collector_20260123.log`
- INFO 레벨 이상의 로그 기록

---
<br>

## ✅ 주의 사항
1) Stop 파일 (`collector.stop`) 생성 시 Collector가 안전하게 종료됨
2) ChromeDriver는 Headless 모드 + 랜덤 User-Agent 적용
3) Kafka Avro 전송 시 Schema 등록 필요
4) Redis 중복 체크 후 신규 데이터만 Kafka 전송
---
