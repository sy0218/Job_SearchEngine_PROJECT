# 📦 consumer.service (Job Detail Scraper)
> 구인구직 사이트 채용 공고에서 **배너 정보 / 본문 텍스트 / 이미지**를 수집하고

> OCR 처리용 Kafka 토픽으로 **이미지 메타 데이터**를 전송하며

> **파싱한 채용 데이터와 이미지 바이너리**를 NFS에 저장하는 **백그라운드 서비스**입니다.

- **systemd 서비스**로 자동 실행 및 관리
- **Kafka → Selenium → Parser → NFS 파이프라인**
- **Selenium + Scrapy** 기반 채용 공고 크롤러  
- Kafka를 통해 **이미지 메타 데이터 전송**  
- NFS를 통해 **NDJSON 데이터 및 이미지 바이너리 저장**  
- 멀티프로세스 병렬 처리  
- 환경 설정 파일로 도메인/잡별 수집 관리 

---
<br>

## 📂 주요 파일 구조
| 파일명 | 설명 |
|--------|------|
| `consumer.service` | systemd 유닛 파일 (서비스 관리) |
| `consumer.sh` | 환경 변수 로드 및 서비스 시작/중지 스크립트 |
| **`consumer.py` (메인)** | **멀티프로세스 기반 채용 공고 수집 및 전송** |
| `job.conf` | 환경 변수 설정 파일 |
| `consumer.properties` | 도메인/URL/XPath/이미지/NDJSON 저장 경로 설정 |
| `config_log.py` | 로그 설정 (날짜별 파일 생성) |
| `common/kafka_hook.py` | Kafka Producer/Consumer 래퍼 |
| `common/crawling_class.py` | Selenium 래퍼, 채용 데이터 파서 |
| `common/job_class.py` | 환경 변수, StopChecker, 데이터 전처리 및 NFS 저장 클래스 |

---
<br>

## ▶️ 서비스 동작 흐름
```plaintext
systemd (consumer.service)
   │
   └─ consumer.py (_main)
          │
          ├─ 환경 변수 및 설정 로드
          ├─ Kafka Consumer + Producer 연결
          ├─ ChromeDriver 브라우저 시작
          │
          ├─ 멀티프로세스 워커 초기화 (ProcessPoolExecutor)
          │
          ├─ Kafka 배치 메시지 수신
          │    ├─ Job URL 접속
          │    ├─ 페이지 대기 & 자동 스크롤
          │    ├─ HTML → Scrapy TextResponse 변환
          │    ├─ 채용 데이터 추출 (배너, 본문 텍스트, 이미지)
          │    ├─ 이미지 바이너리 → NFS 저장
          │    ├─ NDJSON 데이터 → NFS 저장
          │    └─ 이미지 메타 정보 → Kafka OCR 토픽 전송
          │
          └─ Stop 파일 감지 시 안전 종료
```

---
<br>

## 🌟 주요 특징
- 채용 공고 배너/본문/이미지 추출
- 본문 텍스트 정리 (특수문자 제거, 공백 정리)
- 이미지 바이너리 NFS 저장
- 파싱 데이터 NDJSON NFS 저장
- OCR Kafka 토픽으로 이미지 해시 전
- 멀티프로세스로 효율적 수집
- Stop 플래그 감지 시 안전 종료
- 데이터 예시
```json
{
  "domain": "remember",
  "href": "...",
  "company": "...",
  "title": "...",
  "msgid": "...",
  "body_text": "...",
  "body_img": ["0d8dd5659bfb18d2fe4d496a9531b652..."],
  "pay": "...",
  "location": "...",
  "career": "...",
  "education": "...",
  "deadline": "...",
  "type": "..."
}
```

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

## 📋 설정 파일 (consumer.properties)
```ini
# =========================
# Kafka Consumer Partition 설정
# =========================
[partition_num]
num=1

# =========================
# Kafka Poll 옵션
# ========================
[poll_opt]
poll_size=5

# =========================
# 이미지 필터링 옵션
# =========================
[img_bypass]
# 최소 이미지 너비
width=50
# 최소 이미지 높이
height=50
# 최소 이미지 용량( KB )
size=20

# =========================
# 페이지에서 데이터를 가져올 XPath
# =========================
[xpath]
remember.body=//div[@class='sc-70f5b6f6-0 kXwJGP']
remember.banner=//span[contains(normalize-space(), '{kw}')]/following-sibling::*[1]//text()
remember.wait=div[class='sc-884c2c6c-2 jwCPBj']

jobplanet.body=//div[@class='recruitment-detail__box']
jobplanet.banner=//div[contains(@class, 'recruitment-summary')]//dt[contains(., '{kw}')]/following-sibling::dd[1]//text()
jobplanet.wait=div[class='job_body']

wanted.body=//div[@class='JobDescription_JobDescription__paragraph__wrapper__WPrKC']
wanted.banner=//span[contains(@class, 'JobHeader_JobHeader__Tools__Company__Info') and contains(text(), '{kw}')]/text()|//h2[contains(text(), '{kw}')]/following-sibling::span[contains(@class, 'wds')]/text()|//h2[contains(text(), '{kw}')]/following-sibling::*//span[contains(@class, 'wds')]/text()
wanted.wait=section[class='JobContent_JobContent__Qb6DR']

saramin.body=//div[@class='cont']
saramin.banner=//div[contains(@class,'cont')]//dt[normalize-space()='{kw}']/following-sibling::dd[1]/strong/text()|//div[contains(@class,'cont')]//dt[normalize-space()='{kw}']/following-sibling::dd[1]//text()|//div[contains(@class,'status')]//dt[normalize-space()='{kw}']/following-sibling::dd[1]/text()
saramin.wait=div[class='wrap_jv_cont']


# =========================
# 사이트별 크롤링 옵션 & 페이지 없음 텍스트
# =========================
[option]
saramin.setup_flag=n
remember.setup_flag=n
jobplanet.setup_flag=n
wanted.setup_flag=y
no_page_text=페이지를 찾을 수 없어요|페이지가 없습니다|채용정보를 찾을 수 없습니다


# =========================
# 자동 필터 설정 XPath ( 직군 선택 → 적용 버튼까지 순서대로 실행 )
# option 항목의 setup_flag = y 인 사이트에서만 사용
# =========================
[auto_setup]
wanted=//button[.//span[contains(text(), '상세 정보 더 보기')]]


# =========================
# Kafka 직렬화 스키마 파일 경로
# =========================
[schema]
job_header=/work/job_project/schema/kafka/job_header.avsc
```

---
<br>

## ▶️ 서비스 실행
```bash
# 시작
sudo systemctl start consumer.service

# 중지
sudo systemctl stop consumer.service

# 상태 확인
sudo systemctl status consumer.service
```

---
<br>

## 📜 로그
- 로그 파일 위치: `$CONSUMER_LOG_FILE_YYYYMMDD.log`
- 예시: `/work/job_project/logs/consumer_20260128.log`
- INFO 레벨 이상의 로그 기록

---
<br>

## ✅ 주의 사항
1) Stop 파일 (`consumer.stop`) 생성 시 Consumer가 안전하게 종료됨  
2) ChromeDriver는 Headless 모드 + 랜덤 User-Agent 적용  
3) **Kafka Avro 전송 시 Schema 등록 필요**  
4) **NDJSON 데이터와 이미지 바이너리 모두 NFS에 저장 ( NFS 마운트 필수 )**
5) 이미지 Kafka 전송은 **해시값만**  
---
