# 🚚 hadoop_upload.service (Hadoop Upload)
> NFS에 저장된 NDJSON 데이터를 **라인 단위 병합 후 압축**하여 → HDFS로 업로드하고

> 업로드 완료 후 **로컬 NFS 원본 파일 삭제**를 수행하는 **백그라운드 서비스**입니다.

- **systemd 서비스**로 자동 실행 및 관리  
- NFS → 로컬 압축 → HDFS 업로드  
- `LINE_LIMIT` 기준으로 파일 병합 및 업로드  
- 업로드 실패 시 **정리 후 재시작**  
- Stop 파일 감지 시 안전 종료

---
<br>

## 📂 주요 파일 구조
| 파일명 | 설명 |
|--------|------|
| `hadoop_upload.service` | systemd 유닛 파일 (서비스 관리) |
| `hadoop_upload.sh` | 환경 변수 로드 및 서비스 시작/중지 스크립트 |
| **`hadoop_upload.sh` (메인)** | **NFS 파일 병합, 압축, HDFS 업로드** |
| `job.conf` | 환경 변수 설정 파일 |
| `hadoop_upload.properties` | 업로드 경로, 라인 제한, 지연 시간 설정 |
| `functions.sh` | 공통 로깅 함수 (`log_info`, `log_error`) |

---
<br>

## ▶️ 서비스 동작 흐름
```plaintext
systemd (hadoop_upload.service)
   │
   └─ hadoop_upload.sh (_main)
          │
          ├─ 환경 변수 및 설정 로드
          │
          └─ while ( 루프 )
               │
               ├─ NFS 데이터 파일 목록 조회 (시간순 정렬)
               ├─ 각 파일 처리
               │     ├─ 최근 작성 파일 확인 (DELAY_MIN)
               │     ├─ 라인 수 계산 후 큐에 추가
               │     ├─ LINE_LIMIT 도달 시
               │     │     ├─ 파일 병합 & gzip 압축
               │     │     ├─ HDFS 업로드 (hdfs dfs -copyFromLocal)
               │     │     └─ 업로드 성공 시 NFS 원본 삭제
               │     └─ LINE_LIMIT 미달 시 로그
               │
               ├─ Stop 파일 감지 시 안전 종료
               └─ 10초 대기 후 반복
```

---
<br>

## 🌟 주요 특징
- NFS NDJSON 파일 라인 단위 병합 및 gzip 압축
- HDFS 업로드 자동 수행
- 업로드 실패 시 정리 후 재시작
- Stop 파일 감지 시 안전 종료
- LINE_LIMIT 단위로 효율적 배치 업로드
- 데이터 예시: (NFS에 저장된 NDJSON 그대로 HDFS로 업로드)
```json
{"domain":"remember","title":"...","body_text":"...","body_img":["/nfs/img/0d/8d/..."]}
```

---
<br>

## 📋 환경 변수 (job.conf)
```bash
export PYTHONPATH=/work/job_project

# Hadoop Upload
export HD_UPLOAD_CONFIG_PATH=/work/jsy/job_project/hadoop_upload/conf/hadoop_upload.properties
export HD_UPLOAD_WORK_DIR=/work/jsy/job_project/hadoop_upload
export HD_UPLOAD_STOP_DIR=/work/jsy/job_project/hadoop_upload/control
export HD_UPLOAD_STOP_FILE=hadoop_upload.stop
export HD_UPLOAD_LOG_DIR=/work/jsy/job_project/logs/hadoop_upload

# NFS 데이터 경로
export NFS_DATA=/nfs/job_data
export NFS_IMG=/nfs/img

# 공통
export REDIS_HOST=192.168.122.59
export REDIS_PORT=6379
export REDIS_DB=0
export REDIS_PASSWORD=1234

export KAFKA_HOST=192.168.122.60:9092,192.168.122.61:9092,192.56.122.62:9092
export SCHEMA_REGISTRY=http://192.168.122.59:8081
export JOB_TOPIC=job_header_topic
export OCR_TOPIC=ocr_img
export JOB_GROUP_ID=job-group

export POSTGRESQL_HOST=192.168.122.59
export POSTGRESQL_PORT=5432
export POSTGRESQL_DB=job_pro
export POSTGRESQL_USER=sjj
export POSTGRESQL_PASSWORD=1234
```

---
<br>

## 📋 설정 파일 (hadoop_upload.properties)
```bash
# HDFS 업로드 경로
export UPLOAD_DIR=/hdfs_tmp_data
export HADOOP_DIR=/hive/job_project/org

# 업로드 단위 라인 수
export LINE_LIMIT=100

# 최근 작성 파일 대기 시간 (분)
export DELAY_MIN=1
```

---
<br>

## ▶️ 서비스 실행
```bash
# 시작
sudo systemctl start hadoop_upload.service

# 중지
sudo systemctl stop hadoop_upload.service

# 상태 확인
sudo systemctl status hadoop_upload.service
```

---
<br>

## 📜 로그
- 로그 파일 위치: `$HD_UPLOAD_LOG_DIR/hadoop_upload_YYYYMMDD.log`
- 예시: `/work/job_project/logs/hadoop_upload_20260129.log`
- INFO/ERROR 레벨 기록

---
<br>

## ✅ 주의 사항
1) Stop 파일 (`hadoop_upload.stop`) 생성 시 서비스가 안전하게 종료됩니다.  
2) LINE_LIMIT 단위로 NDJSON 파일 병합 및 업로드가 수행됩니다.  
3) 최근 작성된 파일(DELAY_MIN) 처리 시 일정 시간 대기 후 처리합니다.  
4) 업로드 실패 시 로컬 압축 파일과 HDFS 업로드 파일을 삭제 후 재시작합니다.  
5) NFS 원본 파일은 업로드 성공 후 삭제됩니다.  
---
