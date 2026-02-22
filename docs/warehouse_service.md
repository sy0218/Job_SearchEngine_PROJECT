# 🛢️ warehouse.service (Job Data Warehouse)
> 수집·가공된 **채용 공고 데이터와 OCR 결과를 병합**하여 → **형태소 분석을 수행**하고

> Elasticsearch Bulk 업로드용 데이터를 **HDFS에 적재**하는 **백그라운드 서비스**입니다.

- **systemd 서비스**로 자동 실행 및 관리  
- Redis OCR 결과 대기 및 병합 처리  
- txid 기반 스케일아웃 병렬 처리 (cluster_num / process_num)
- PostgreSQL 기반 처리 상태 관리  
- Hadoop(HDFS) 연동 데이터 처리  
- Kiwi + spaCy 기반 형태소 분석  
- Stop 파일 기반 안전 종료  

---
<br>

## 🔄 Warehouse Pipline
![Pipline](https://github.com/user-attachments/assets/77cdbdcd-280f-4330-8266-93911d5d2672)

---
<br>

## 📂 주요 파일 구조
| 파일명 | 설명 |
|------|------|
| `warehouse.service` | systemd 유닛 파일 (서비스 관리) |
| `warehouse.sh` | 환경 변수 로드 및 서비스 시작/중지 스크립트 |
| **`warehouse.py` (메인)** | **HDFS → Redis → 형태소 분석 → HDFS 적재** |
| `job.conf` | 환경 변수 설정 파일 |
| `warehouse.properties` | SQL 쿼리 및 HDFS 경로 설정 |
| `config_log.py` | 로그 설정 (날짜별 파일 생성) |
| `common/redis_hook.py` | Redis 연결 및 데이터 처리 |
| `common/postgres_hook.py` | PostgreSQL 연결 및 쿼리 처리 |
| `common/hdfs_hook.py` | HDFS 파일 입출력 처리 |
| `common/morph_analyzer.py` | 형태소 분석 (Kiwi + spaCy) |
| `common/job_class.py` | 환경 변수, StopChecker, 데이터 전처리 유틸 |

---
<br>

## ▶️ 서비스 동작 흐름
```plaintext
systemd (warehouse.service)
   │
   └─ docker exec warehouse
          │
          └─ warehouse.sh start
                 │
                 └─ warehouse.py (_main)
                        │
                        ├─ 환경 변수 및 설정 로드
                        ├─ Redis / PostgreSQL / HDFS 연결
                        ├─ 형태소 분석기 초기화
                        │
                        └─ 메인 루프 시작
                             ├─ Stop 파일 감지
                             │    └─ 감지 시 안전 종료
                             │
                             ├─ 처리 대상 파일 조회 (PostgreSQL)
                             │    └─ txid % cluster_num == process_num 조건 필터링
                             │    └─ 대상 없을 경우 대기 후 재시도
                             │
                             ├─ HDFS gzip NDJSON 파일 읽기
                             ├─ Redis OCR 결과 대기 및 병합
                             │
                             ├─ 본문 + OCR 텍스트 형태소 분석
                             ├─ Elasticsearch Bulk 포맷 생성
                             │
                             ├─ Bulk 데이터 HDFS gzip 업로드
                             ├─ 처리 완료 상태 DB 커밋
                             │
                             └─ 다음 배치 처리
```

---
<br>

## 🌟 주요 특징
- **txid 기반 병렬 분산 처리 (cluster_num / process_num 기준)**
- HDFS gzip NDJSON 파일 처리
- Redis 기반 OCR 결과 대기 및 병합
- 본문 + 이미지 OCR 텍스트 통합 처리
- 형태소 분석 기반 검색 토큰 생성
- Elasticsearch Bulk 업로드 포맷 생성
- 결과 데이터 HDFS gzip 적재
- Stop 파일 기반 안전 종료
- **데이터 예시 (ES Bulk) ⤵**
```json
{ "index": { "_index": "job_postings_v1", "_id": "msgid" } }
{
  "domain": "...",
  "company": "...",
  "title": "...",
  "body_text": "...",
  "morph": ["python", "데이터", "엔지니어"],
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
export ES_JOB_INDEX=job_postings_v1

# nfs
export NFS_DATA=/nfs/job_data
export NFS_IMG=/nfs/img
```

---
<br>

## 📋 설정 파일 (warehouse.properties)
```ini
[option]
process_num=1
cluster_num=3

[sql]
select_hadoop_org=SELECT file_path, txid FROM job.hadoop_org WHERE event_check IS NULL and MOD(txid, %s) = %s ORDER BY txid LIMIT 1;
update_hadoop_event=UPDATE job.hadoop_event SET event_check = TRUE WHERE event_check IS NULL and txid = %s and file_path = %s

[dir]
hadoop_dir=/hive/job_project/new
```

---
<br>

## ▶️ 서비스 실행
```bash
# 시작
sudo systemctl start warehouse.service

# 중지
sudo systemctl stop warehouse.service

# 상태 확인
sudo systemctl status warehouse.service
```

---
<br>

## 📜 로그
- 로그 파일 위치: `$WAREHOUSE_LOG_FILE_YYYYMMDD.log`
- 예시: `/work/job_project/logs/warehouse/warehouse_20260128.log`

---
<br>

## ✅ 주의 사항
1) Stop 파일 (`warehouse.stop`) 생성 시 서비스가 안전 종료됨
2) **Redis OCR 데이터가 준비되지 않으면 대기 후 재시도**
3) **HDFS 업로드는 Elasticsearch Bulk 포맷 기준**
4) **gzip NDJSON 기반 대용량 처리 최적화**
5) **처리 완료 후 반드시 PostgreSQL 커밋 수행**
6) **병렬 처리 환경에서 각 서버는 서로 다른 process_num을 사용해야 하며, cluster_num 설정은 모든 노드에서 동일해야 함**
---
