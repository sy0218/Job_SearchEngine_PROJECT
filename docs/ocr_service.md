# 🧠 ocr.service (Image OCR Processor)
> Kafka로 전달된 이미지 메타 데이터(해시값)를 기반으로  

> NFS에 저장된 이미지를 불러와 **OCR 텍스트를 추출**하고
  
> 결과를 **Redis에 캐싱**하는 **백그라운드 OCR 처리 서비스**입니다.

- **systemd 서비스**로 자동 실행 및 관리  
- **EasyOCR 기반** 이미지 텍스트 추출  
- Kafka Consumer를 통해 **이미지 처리 대상 수신**  
- NFS에 저장된 이미지 파일 사용  
- OCR 결과를 **Redis Key-Value 형태로 저장**  
- Stop 파일 기반 **안전 종료 지원**

---
<br>

## 📂 주요 파일 구조
| 파일명 | 설명 |
|------|------|
| `ocr.service` | systemd 유닛 파일 (Docker 기반 서비스 관리) |
| `ocr.sh` | 환경 변수 로드 및 서비스 시작/중지 스크립트 |
| **`ocr.py` (메인)** | **Kafka 기반 OCR 순차 처리 메인 로직** |
| `job.conf` | 환경 변수 설정 파일 |
| `ocr.properties` | Kafka 파티션 / Poll 옵션 / OCR 신뢰도 설정 |
| `config_log.py` | 날짜별 로그 파일 설정 |
| `common/hook_class.py` | Kafka / Redis Hook |
| `common/job_class.py` | 환경 변수 로드, StopChecker |

---
<br>

## ▶️ 서비스 동작 흐름
```plaintext
systemd (ocr.service)
   │
   └─ docker exec ocr ocr.sh start
          │
          └─ ocr.py (_main)
                 │
                 ├─ 환경 변수 및 설정 로드
                 │    ├─ OCR 설정 (confidence)
                 │    └─ Kafka / Redis / NFS 정보
                 │
                 ├─ Kafka Consumer 연결 (ocr_img 토픽)
                 ├─ Redis 연결 (이미지 결과 캐시)
                 ├─ EasyOCR Reader 초기화
                 │
                 ├─ Kafka 메시지 배치 수신
                 │    ├─ 이미지 해시값 수신
                 │    ├─ NFS 경로 변환
                 │    ├─ Redis 중복 여부 확인
                 │    ├─ 이미지 OCR 처리
                 │    └─ OCR 결과 Redis 저장
                 │
                 └─ Stop 파일 감지 시 안전 종료
```

---
<br>

## 🌟 주요 특징
- Kafka 이미지 토픽 기반 OCR 처리
- 이미지 해시 → NFS 경로 자동 변환
- OCR 신뢰도(confidence) 기반 텍스트 필터링
- Redis 중복 체크로 **중복 OCR 방지**
- OCR 결과 Redis 캐시 저장
- Stop 파일 기반 graceful shutdown
- GPU 미사용 (CPU OCR)

---
<br>

## 📋 환경 변수 (job.conf)
```bash
export PYTHONPATH=/work/job_project

# OCR
export OCR_CONFIG_PATH=/work/job_project/ocr/conf/ocr.properties
export OCR_WORK_DIR=/work/job_project/ocr
export OCR_STOP_DIR=/work/job_project/ocr/control
export OCR_STOP_FILE=ocr.stop
export OCR_LOG_FILE=/work/job_project/logs/ocr/ocr

# Redis
export REDIS_HOST=192.168.122.59
export REDIS_PORT=6379
export REDIS_DB_IMG=1
export REDIS_PASSWORD=1234

# Kafka
export KAFKA_HOST=192.168.122.60:9092,192.168.122.61:9092,192.56.122.62:9092
export OCR_TOPIC=ocr_img
export OCR_GROUP_ID=ocr-group

# NFS
export NFS_IMG=/nfs/img
```

---
<br>

## 📋 설정 파일 (ocr.properties)
```ini
[partition_num]
num=0

[poll_opt]
poll_size=1

[nfs_path]
img=/nfs/img

[ocr]
confidence=0.6
```

---
<br>

## ▶️ 서비스 실행
```bash
# 시작
sudo systemctl start ocr.service

# 중지 (stop 파일 생성 → 안전 종료)
sudo systemctl stop ocr.service

# 상태 확인
sudo systemctl status ocr.service
```

---
<br>

## 📜 로그
- 로그 파일 위치: `$OCR_LOG_FILE_YYYYMMDD.log`
- 예시: `/work/job_project/logs/ocr/ocr_20260131.log`

---
<br>

## 🧾 Redis 저장 데이터 예시
```plaintext
Key   : <image_hash>
Value: "추출된 OCR 텍스트 ..."
```
- 동일 이미지 해시 재수신 시 OCR Skip

---
<br>

## ✅ 주의 사항
1) Stop 파일 (`ocr.stop`) 생성 시 OCR 서비스가 안전하게 종료됨  
2) Kafka 메시지는 이미지 **해시값(파일명)** 만 전달됨  
3) OCR 대상 이미지는 반드시 NFS 경로에 존재해야 함  
4) Redis에 동일 이미지 해시가 존재할 경우 OCR 처리는 Skip 됨  
5) OCR 신뢰도(`confidence`) 기준에 따라 텍스트가 필터링될 수 있음
---
