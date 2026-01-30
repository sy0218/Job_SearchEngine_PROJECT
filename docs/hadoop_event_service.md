# 🕵️ hadoop_event.service (HDFS Close Event Watcher)
> HDFS에 업로드된 파일의 **CLOSE 이벤트**를 감시하고 이벤트 발생 시 **PostgreSQL에 파일 경로 및 크기 기록**을 수행하는 **백그라운드 서비스**입니다.

- **systemd 서비스**로 자동 실행 및 관리  
- HDFS CLOSE 이벤트 실시간 감시 (`DFSInotifyEventInputStream`)  
- 감시 경로는 `watch.path` 기준 필터링  
- 이벤트 발생 시 **로그 기록 및 DB 적재**  
- 종료 시 SIGTERM 신호로 안전 종료

---
<br>

## 📂 주요 파일 구조
| 파일명 | 설명 |
|--------|------|
| `hadoop_event.service` | systemd 유닛 파일 (서비스 관리) |
| `hadoop_event.sh` | 환경 변수 로드 및 서비스 실행 스크립트 |
| **`HdfsCloseWatcher.java` (메인)** | **HDFS CLOSE 이벤트 감시 및 PostgreSQL 적재** |
| `job.conf` | 환경 변수 설정 파일 |
| `hadoop_event.properties` | 감시 대상 HDFS 경로 설정 (`watch.path`) |

---
<br>

## 🛠 컴파일 방법
```bash
# 하둡 라이브러리 및 PostgreSQL JDBC 포함하여 컴파일
javac -classpath "$(hadoop classpath --glob):/work/jsy/lib/postgresql-42.7.3.jar" HdfsCloseWatcher.java
```
- `$(hadoop classpath --glob)` : 하둡 관련 모든 jar 포함
- PostgreSQL JDBC jar 위치 지정 (`/work/jsy/lib/postgresql-42.7.3.jar`)
- 컴파일 후 `.class` 파일이 생성되어 실행 가능

---
<br>

## ▶️ 서비스 동작 흐름
```plaintext
systemd (hadoop_event.service)
   │
   └─ hadoop_event.sh
          │
          ├─ 환경 변수 및 설정 로드 (job.conf, hadoop_event.properties)
          │
          └─ HdfsCloseWatcher.main()
               │
               ├─ PostgreSQL 연결 초기화
               ├─ HDFS Configuration 로드
               ├─ DFSInotifyEventInputStream 생성
               ├─ 로그 파일 생성 (hdfs_close_YYYYMMDD.log)
               │
               └─ 이벤트 감시 루프 (블로킹)
                    │
                    ├─ EventBatch 수신
                    └─ 각 Event 처리
                          ├─ CLOSE 이벤트 필터
                          ├─ 감시 경로(`watch.path`) 필터
                          ├─ `_COPYING_` 제거 후 로그 기록
                          └─ PostgreSQL에 `file_path`, `file_size` INSERT
```

---
<br>

## 🌟 주요 특징
- HDFS CLOSE 이벤트 실시간 감시
- 이벤트 발생 시 로그 및 PostgreSQL DB 자동 기록
- 감시 경로 필터링 (`watch.path`)
- SIGTERM 신호로 종료 가능
- 블로킹 루프 기반으로 이벤트를 놓치지 않고 처리
- 로그 예시 ⤵
```plaintext
[INIT] PostgreSQL connected
[START] HDFS CLOSE watcher started
[WATCH] Path prefix: /hive/job_project
[CLOSE] path=/hive/job_project/org/20260129102650.gz, fileSize=143232
[CLOSE] path=/hive/job_project/org/20260129134249.gz, fileSize=127496
[CLOSE] path=/hive/job_project/org/20260129141543.gz, fileSize=139498
[CLOSE] path=/hive/job_project/org/20260129141543.gz, fileSize=139498
~
```

---
<br>

## 📋 환경 변수 (job.conf)
```bash
export PYTHONPATH=/work/job_project
export JOB_LIB=/work/jsy/job_project/lib

# Collector
export COLLECTOR_CONFIG_PATH=/work/job_project/collector/conf/collector.properties
export COLLECTOR_WORK_DIR=/work/job_project/collector
export COLLECTOR_STOP_DIR=/work/job_project/collector/control
export COLLECTOR_STOP_FILE=collector.stop
export COLLECTOR_LOG_DIR=/work/job_project/logs/collector

# Consumer
export CONSUMER_CONFIG_PATH=/work/job_project/consumer/conf/consumer.properties
export CONSUMER_WORK_DIR=/work/job_project/consumer
export CONSUMER_STOP_DIR=/work/job_project/consumer/control
export CONSUMER_STOP_FILE=consumer.stop
export CONSUMER_LOG_DIR=/work/job_project/logs/consumer

# Hadoop Upload
export HD_UPLOAD_CONFIG_PATH=/work/jsy/job_project/hadoop_upload/conf/hadoop_upload.properties
export HD_UPLOAD_WORK_DIR=/work/jsy/job_project/hadoop_upload
export HD_UPLOAD_STOP_DIR=/work/jsy/job_project/hadoop_upload/control
export HD_UPLOAD_STOP_FILE=hadoop_upload.stop
export HD_UPLOAD_LOG_DIR=/work/jsy/job_project/logs/hadoop_upload

# Hadoop Event
export HD_EVENT_CONFIG_PATH=/work/jsy/job_project/hadoop_event/conf/hadoop_event.properties
export HD_EVENT_WORK_DIR=/work/jsy/job_project/hadoop_event
export HD_EVENT_LOG_DIR=/work/jsy/job_project/logs/hadoop_event

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
export OCR_TOPIC=ocr_img
export JOB_GROUP_ID=job-group

# PostgreSQL
export POSTGRESQL_HOST=192.168.122.59
export POSTGRESQL_PORT=5432
export POSTGRESQL_DB=job_pro
export POSTGRESQL_USER=sjj
export POSTGRESQL_PASSWORD=1234

# NFS
export NFS_DATA=/nfs/job_data
export NFS_IMG=/nfs/img
```

---
<br>

## 📋 설정 파일 (hadoop_event.properties)
```properties
# 감시 대상 HDFS 경로
watch.path=/hive/job_project
```

---
<br>

## ▶️ 서비스 실행
```bash
# 시작
sudo systemctl start hadoop_event.service

# 중지
sudo systemctl stop hadoop_event.service

# 상태 확인
sudo systemctl status hadoop_event.service
```

---
<br>

## 📜 로그
- 로그 파일 위치: `$HD_EVENT_LOG_DIR/hdfs_close_YYYYMMDD.log`
- 예시: `/work/jsy/job_project/logs/hadoop_event/hdfs_close_20260129.log`

---
<br>

## ✅ 주의 사항
1) `watch.path`에 맞는 **HDFS CLOSE 이벤트**만 처리됩니다.  
2) 이벤트 발생 시 `_COPYING_` 접미어 제거 후 로그 기록 및 DB 적재가 수행됩니다.  
3) PostgreSQL 연결 실패 시 서비스가 종료됩니다.  
4) 이벤트 감시 루프는 블로킹 방식으로 동작하므로, 이벤트를 놓치지 않고 실시간 처리됩니다.  
5) **로그와 DB INSERT가 실패**할 경우 서비스가 종료되며 재시작이 필요합니다.
---
