# 🔍 **ocr.service** - 통합 테스트
> OCR 데몬 서비스의 **통합 테스트 문서**

---
<br>

## 🎯 테스트 목적
- **OCR 서비스의 전체 이미지 처리 파이프라인 검증**
- Kafka / NFS / Redis 연동 정상 여부 확인
- Stop 제어 및 안정 종료 테스트
- OCR 처리 안정성 및 예외 대응 검증
- 시스템 리소스 사용량 모니터링

---
<br>

## 🧩 테스트 환경
| 항목 | 내용 |
|------|------|
| OS | Ubuntu 22.04 |
| Python | 3.10.12 |
| Docker | 사용 |
| OCR Engine | EasyOCR (CPU) |
| Kafka | broker: 3.6.2 |
| Redis | host: 7.4.7 |
| NFS | 마운트된 공유 스토리지 |
| Grafana | 모니터링 활성 |

---
<br>

## ▶️ 사전 준비
```bash
# 서비스 상태 확인
sudo systemctl status ocr.service

# Kafka 토픽 확인
kafka-topics.sh --list --bootstrap-server <broker>

# Redis 연결 테스트
redis-cli -h <redis_host> -p 6379 ping

# NFS 접근 테스트
ls -l /nfs/img
```

---
<br>

# 🔍 테스트 시나리오
## **✅ 1. 서비스 정상 기동 테스트**
### ✔ 목적 : OCR 서비스가 정상적으로 시작되는지 확인
---
### ✔ 절차
1) 서비스 시작
2) 로그 확인
3) OCR Reader 초기화 여부 확인
```bash
systemctl start ocr.service
systemctl status ocr.service
```
---
### **✔ 검증 항목 ( 정상 확인 )**
✅ 서비스 상태: active (running)  
✅ EasyOCR Reader 정상 초기화  
✅ Kafka Consumer & Redis 연결 성공  
✅ ERROR 로그 없음  

---
<br>

## **✅ 2. Kafka 이미지 메시지 처리 테스트**
### ✔ 목적 : Kafka 이미지 해시 메시지를 정상 처리하는지 확인
---
### ✔ 절차
1) Kafka에 테스트 이미지 해시 메시지 생성
2) Consumer 로그 확인
3) Redis OCR 결과 저장 여부 확인
---
### **✔ 검증 항목 ( 정상 확인 )**
✅ Kafka 메시지 수신 성공  
✅ NFS 이미지 정상 로드  
✅ OCR 텍스트 추출 성공  
✅ Redis에 OCR 결과 저장  

---
<br>

## **✅ 3. Redis 중복 처리 테스트**
### ✔ 목적 : 동일 이미지 재수신 시 OCR Skip 확인
---
### ✔ 절차
1) 동일 이미지 해시 재전송
2) Redis 캐시 확인
3) 로그 확인
---
### **✔ 검증 항목 ( 정상 확인 )**
✅ Redis 중복 감지  
✅ OCR 재처리 Skip  
✅ Skip 로그 기록  

---
<br>

## **✅ 4. Stop 파일 종료 테스트**
### ✔ 목적 : 목적 : Stop 파일 생성 시 안전 종료 확인
---
### ✔ 절차
```bash
touch /work/job_project/ocr/control/ocr.stop
```
---
### **✔ 검증 항목 ( 정상 확인 )**
✅ Stop 파일 감지 후 graceful shutdown  
✅ Kafka Consumer 정상 종료  
✅ 로그 기록 완료 

---
<br>

## **✅5. 장시간 실행 안정성 테스트**
### ✔ 목적 : 24시간 이상 실행 시 자원 누수 확인
---
### **✔ 검증 항목 ( 정상 확인 )**
✅ 메모리 누수 없음  
✅ Kafka 처리 정상 유지  
✅ Redis 저장 정상 동작  

---
<br>

## 📊 리소스 모니터링 (Grafana)
> OCR 서비스 기동 전/후 리소스 비교

| 📌 지표 | 📈 Grafana 쿼리 | 🔍 측정 결과 |
|--------|----------------|-------------|
| **CPU I/O Wait (iowait)** | `avg(rate(node_cpu_seconds_total{instance="192.168.122.65:9100", mode="iowait"}[1m])) * 100` | **0.02% (기동 전)** → **1.47% (기동 후)** |
| **CPU 사용률** | `100 - (avg(rate(node_cpu_seconds_total{instance="192.168.122.65:9100", mode="idle"}[1m])) * 100)` | **0.8% (기동 전)** → **27.6% (기동 후)** |
| **Load Average (1m)** | `node_load1{instance="192.168.122.65:9100"}` | **0.2 (기동 전)** → **1.68 (기동 후)** |
| **메모리 사용률** | `(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100` | **37% (기동 전)** → **38.9% (기동 후)** |

---
<br>

## 📜 로그 확인
```bash
tail -f /work/job_project/logs/ocr/*.log
```
---
### **✔ 검증 항목 (정상 확인)**
✅ OCR 처리 성공 로그 확인  
✅ Redis 저장 로그 확인  
✅ ERROR 로그 없음

---
<br>

## 📝 테스트 결과 기록
| 테스트 항목               | 결과      | 비고          |
| :------------------------: | :------: | :------------ |
| 서비스 기동               | **PASS** |                |
| Kafka 메시지 처리         | **PASS** |                |
| Redis 중복 처리            | **PASS** |                |
| Stop 파일 종료        | **PASS** |                |
| 이미지 예외 처리                  | **PASS** |                |
| 장시간 안정성             | **PASS** |                |

---
<br>

## 🚨 이슈 기록

| 시간 | 증상 | 원인 | 조치 |
|------|------|------|------|
| 2026-02-09 | P 모드 이미지 처리 중 OOM 발생 | EasyOCR P 모드 이미지 입력 | 이미지 RGB 변환 적용 (`img.convert('RGB')`) ✅ |
| 2026-02-09 | OpenCV remap 오류 발생 | 초대형 이미지 | max_side 기준 자동 리사이즈 로직 적용 ✅ |

---
<br>

# 🏆 테스트 결론 (요약)
**OCR 서비스 통합 테스트 결과**

---
## 1. 전체 안정성
- Kafka → NFS → OCR → Redis 전체 파이프라인 정상 동작
- 이미지 예외 처리 로직 적용 후 안정성 확보
- Stop 기반 안전 종료 정상 작동
- 정합성 검증 결과 Kafka와 [ Skip + Redis ] 데이터 일치
---
## 2. 성능 평가
- CPU/메모리/Load 안정적 유지
- OCR 처리 중 시스템 과부하 없음
- Grafana 모니터링 정상
---
## 3. 개선 필요 사항
- OCR 성능 개선 여지 있음
---
