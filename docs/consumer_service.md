# 📦 consumer.service (Job Detail Scraper)
> 구인구직 사이트 채용 공고에서 **배너 정보, 본문 텍스트, 이미지**를 수집하고

> OCR 처리용 토픽으로 **이미지 메타 데이터**를 전송하며

> **파싱한 채용 데이터와 이미지 바이너리**를 NFS에 저장하는 **백그라운드 서비스**입니다.

- **systemd 서비스**로 자동 실행 및 관리  
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
| **`consumer.py` (메인)** | 멀티프로세스 기반 채용 공고 수집 및 전송 |
| `job.conf` | 환경 변수 설정 파일 |
| `consumer.properties` | 도메인/URL/XPath/이미지/NDJSON 저장 경로 설정 |
| `config_log.py` | 로그 설정 (날짜별 파일 생성) |
| `common/hook_class.py` | Kafka / Redis / PostgreSQL Hook |
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
- Kafka OCR 토픽 전송: 이미지 파일명만 전송
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
  "body_img": ["/nfs/img/0d/8d/0d8dd5659bfb18d2fe4d496a9531b652cf851a69b6b13ddce6364e81772957ae"],
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

# Collector
export COLLECTOR_CONFIG_PATH=/work/job_project/collector/conf/collector.properties
export COLLECTOR_WORK_DIR=/work/job_project/collector
export COLLECTOR_STOP_DIR=/work/job_project/collector/control
export COLLECTOR_STOP_FILE=collector.stop
export COLLECTOR_LOG_FILE=/work/job_project/logs/collector

# Consumer
export CONSUMER_CONFIG_PATH=/work/job_project/consumer/conf/consumer.properties
export CONSUMER_WORK_DIR=/work/job_project/consumer
export CONSUMER_STOP_DIR=/work/job_project/consumer/control
export CONSUMER_STOP_FILE=consumer.stop
export CONSUMER_LOG_FILE=/work/job_project/logs/consumer

# Redis (사용 안함)
export REDIS_HOST=192.168.122.59
export REDIS_PORT=6379
export REDIS_DB=0
export REDIS_PASSWORD=1234
export REDIS_JOBHEAD_KEY=job_set

# Kafka
export KAFKA_HOST=192.168.122.60:9092,192.168.122.61:9092,192.56.122.62:9092
export SCHEMA_REGISTRY=http://192.168.122.59:8081
export JOB_TOPIC=job_header_topic
export OCR_TOPIC=ocr_img
export JOB_GROUP_ID=job-group

# PostgreSQL
export POSTGRESQL_HOST=192.168.122.59
export POSTGRESQL_PORT=5432
export POSTGRESQL_DB=job_pro
export POSTGRESQL_USER=sjj
export POSTGRESQL_PASSWORD=1234
```

---
<br>

## 📋 설정 파일 (consumer.properties)
```ini
[partition_num]
num=0

[poll_opt]
poll_size=3

[img_bypass]
width=50
height=50
size=10

[nfs_path]
img=/nfs/img
data=/nfs/job_data

[xpath]
remember.body=//div[@class='sc-70f5b6f6-0 kXwJGP']
remember.banner=//div[@class='sc-a34accef-0 cBEpAk']//span[contains(text(), '{kw}')]/following-sibling::span/text()|//div[@class='sc-a34accef-0 cBEpAk']//span[contains(text(), '{kw}')]/following-sibling::div//span/text()
remember.wait=#app-body

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
3) Kafka Avro 전송 시 Schema 등록 필요  
4) NDJSON 데이터와 이미지 바이너리 모두 NFS에 저장  
5) 이미지 Kafka 전송은 **파일명만**  
---
