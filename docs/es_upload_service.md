# 📤 es_upload.service (Elasticsearch Upload Service)

> HDFS에 저장된 **Elasticsearch Bulk NDJSON gzip 파일을 읽어** → **Elasticsearch로 업로드**하고  

> 처리 완료 상태를 **PostgreSQL에 기록**하는 **백그라운드 서비스**입니다.

- **systemd 서비스** 기반 자동 실행
- HDFS gzip NDJSON 스트리밍 처리
- txid 기반 스케일아웃 병렬 처리 (cluster_num / process_num)
- Elasticsearch Bulk 업로드
- PostgreSQL 처리 상태 관리
- Chunk 단위 업로드 최적화
- Stop 파일 기반 안전 종료

---
<br>

## 🔄 Elasticsearch Upload Pipline
![Pipline](https://github.com/user-attachments/assets/5f3b281d-2950-44d9-826f-5d462aeef681)

---
<br>

## 📂 주요 파일 구조

| 파일명 | 설명 |
|------|------|
| `es_upload.service` | systemd 유닛 파일 (서비스 관리) |
| `es_upload.sh` | 환경 변수 로드 및 서비스 시작/중지 스크립트 |
| **`es_upload.py` (메인)** | **HDFS → Elasticsearch Bulk 업로드 → DB 커밋** |
| `job.conf` | 환경 변수 설정 파일 |
| `es_upload.properties` | SQL 쿼리 및 업로드 설정 |
| `config_log.py` | 로그 설정 (날짜별 파일 생성) |
| `common/postgres_hook.py` | PostgreSQL Hook |
| `common/hdfs_hook.py` | HDFS Hook |
| `common/es_hook.py` | Elasticsearch Hook |
| `common/job_class.py` | 환경 변수 및 StopChecker |

---
<br>

## ▶️ 서비스 동작 흐름

```plaintext
systemd (es_upload.service)
   │
   └─ docker exec es_upload
          │
          └─ es_upload.sh start
                 │
                 └─ es_upload.py (_main)
                        │
                        ├─ 환경 변수 및 설정 로드
                        ├─ PostgreSQL / HDFS / Elasticsearch 연결
                        │
                        └─ 메인 루프 시작
                             ├─ Stop 파일 감지
                             │    └─ 감지 시 안전 종료
                             │
                             ├─ 처리 대상 파일 조회 (PostgreSQL)
                             │    └─ txid % cluster_num == process_num 조건 필터링
                             │    └─ 대상 없으면 대기 후 재시도
                             │
                             ├─ HDFS gzip NDJSON 파일 읽기
                             ├─ Bulk Generator 생성
                             │
                             ├─ Elasticsearch Chunk 업로드
                             ├─ 처리 완료 DB 커밋
                             │
                             └─ 다음 배치 처리
```

---
<br>

## 🌟 주요 특징
- txid 기반 병렬 분산 처리 (cluster_num / process_num 기준)
- HDFS gzip NDJSON 스트리밍 처리
- Elasticsearch Bulk Chunk 업로드
- 메모리 절약형 Generator 방식 처리
- 대용량 파일 실시간 스트리밍
- PostgreSQL 기반 처리 상태 관리
- Stop 파일 기반 안전 종료
---
### 📦 Elasticsearch Bulk 포맷 예시
```json
{ "index": { "_index": "job_postings_v1", "_id": "msgid" } }
{
  "domain": "...",
  "company": "...",
  "title": "...",
  "body_text": "...",
  "morph": ["python", "데이터", "엔지니어"]
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

## 📋 설정 파일 (es_upload.properties)
```ini
[option]
process_num=0
cluster_num=3

[sql]
select_hadoop_new=SELECT file_path, txid FROM job.hadoop_new WHERE event_check IS NULL and MOD(txid, %s)= %s ORDER BY txid LIMIT 1;
update_hadoop_event=UPDATE job.hadoop_event SET event_check = TRUE WHERE event_check IS NULL and txid = %s and file_path = %s

[es]
chunk=100
timeout=300
```

---
<br>

## ▶️ 서비스 실행
```bash
# 시작
sudo systemctl start es_upload.service

# 중지
sudo systemctl stop es_upload.service

# 상태 확인
sudo systemctl status es_upload.service
```

---
<br>

## 📜 로그
- 로그 파일 위치: `$ES_UPLOAD_LOG_FILE_YYYYMMDD.log`
- 예시: `/work/job_project/logs/es_upload/es_upload_20260128.log`

---
<br>

## ✅ 주의 사항
1) Stop 파일 (`es_upload.stop`) 생성 시 안전 종료됨
2) HDFS 파일은 반드시 **gzip NDJSON Bulk 포맷**이어야 함
3) Elasticsearch 업로드는 **Chunk 단위로** 처리됨
4) **업로드 완료 후 PostgreSQL 상태가 커밋됨**
5) 처리 완료 후 반드시 PostgreSQL 커밋 수행
6) **병렬 처리 환경에서 각 서버는 다른 process_num을 사용해야하며, cluster_num 설정은 모든 노드에서 동일 해야 함**
---
