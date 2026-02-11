# 📡 **collector.service** - 통합 테스트

> Collector 데몬 서비스의 **통합 테스트 문서**

---
<br>

## 🎯 테스트 목적

- **Collector 서비스의 전체 크롤링 파이프라인 검증**
- Redis / Kafka 연동 정상 여부 확인
- Stop 제어 및 안정 종료 테스트
- 장시간 실행 시 안정성 검증
- 시스템 리소스 사용량 모니터링

---
<br>

## 🧩 테스트 환경

| 항목 | 내용 |
|------|------|
| OS | Ubuntu 22.04 |
| Python | 3.10.12 |
| Docker | 사용 |
| Chrome | 버전: 143.0.7499.192 |
| Redis | host: 7.4.7 |
| Kafka | broker: 3.6.2 |
| Grafana | 모니터링 활성화 |

---
<br>

## ▶️ 사전 준비
```bash
# 서비스 상태 확인
sudo systemctl status collector.service

# Redis 연결 확인
redis-cli ping

# Kafka 브로커 확인
kafka-topics.sh --list --bootstrap-server <broker>
```

---
<br>

# 🔍 테스트 시나리오
## **✅ 1. 서비스 정상 기동 테스트**
### ✔ 목적 : Collector 서비스가 정상적으로 시작되는지 확인
---
### ✔ 절차
1) 서비스 시작
2) 로그 확인
3) Chrome 실행 여부 확인
```bash
sudo systemctl start collector.service
sudo systemctl status collector.service
```
---
### **✔ 검증 항목 ( 정상 확인 )**
✅ 서비스 상태: active (running)  
✅ 오류 로그 없음  
✅ Chrome 프로세스 정상 실행  

---
<br>

## **✅ 2. 크롤링 데이터 수집 테스트**
### ✔ 목적 : 채용 데이터가 정상 수집되는지 확인
---
### ✔ 절차
1) 크롤링 실행 로그 확인
2) Redis 중복 체크 확인
3) Kafka 메시지 전송 확인
---
### **✔ 검증 항목 ( 정상 확인 )**
✅ 채용 데이터 파싱 성공  
✅ Redis key 정상 저장  
✅ Kafka topic 메시지 증가  

---
<br>

## **✅ 3. Stop 파일 종료 테스트**
### ✔ 목적 : Stop 파일 생성 시 안전 종료 확인
---
### ✔ 절차
```bash
systemctl stop collector.service
```
---
### **✔ 검증 항목 ( 정상 확인 )**
✅ Collector 안전 종료  
✅ ChromeDriver 종료  
✅ 로그에 종료 메시지 기록  

---
<br>

## **✅ 4. Redis 중복 필터 테스트**
### ✔ 목적 : 중복 데이터가 Kafka로 전송되지 않는지 확인
---
### ✔ 절차
1) 동일 URL 재수집
2) Redis key 확인
---
### **✔ 검증 항목 ( 정상 확인 )**
✅ 중복 데이터 Kafka 미전송  
✅ Redis 정상 동작  

---
<br>

## **✅ 5. 장시간 실행 안정성 테스트**
### ✔ 목적 : 24시간 이상 실행 시 안정성 검증
---
### **✔ 검증 항목 ( 정상 확인 )**
✅ 메모리 누수 없음  
✅ 크롤링 지속 수행  
✅ 프로세스 종료 없음  

---
<br>

## 📊 리소스 모니터링 (Grafana)
> **Collector 서비스 기동 전/후 리소스 비교**

| 📌 지표 | 📈 Grafana 쿼리 | 🔍 측정 결과 |
|--------|----------------|-------------|
| **CPU I/O Wait (iowait)** | `avg(rate(node_cpu_seconds_total{instance="192.168.122.65:9100", mode="iowait"}[1m])) * 100` | **0.005% (기동 전)** → **0.0286% (기동 후)** |
| **CPU 사용률** | `100 - (avg(rate(node_cpu_seconds_total{instance="192.168.122.65:9100", mode="idle"}[1m])) * 100)` | **1% (기동 전)** → **22.2% (기동 후)** |
| **Load Average (1m)** | `node_load1{instance="192.168.122.65:9100"}` | **0.1 (기동 전)** → **2.7 (기동 후)** |
| **메모리 사용률** | `(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100` | **34% (기동 전)** → **37% (기동 후)** |

---

### **✔ 검증 항목 ( 정상 확인 )**
✅ CPU 및 Load Average는 서비스 기동 후 증가했으나 **안정적인 범위**
✅ 메모리 사용률 변화는 **미미**
✅ I/O Wait는 **매우 낮은 수준 유지**

---
<br>

## 📜 로그 확인
```bash
tail -f /work/job_project/logs/collector/*.log
```
---
### **✔ 검증 항목 ( 정상 확인 )**
✅ ERROR 로그 없음
✅ 크롤링 정상 진행
✅ Kafka 전송 로그 확인

---
<br>

## 📝 테스트 결과 기록
| 테스트 항목       | 결과      | 비고          |
| :----------------: | :------: | :------------ |
| 서비스 기동       | **PASS** |                |
| 크롤링 수집       | **PASS** |                |
| Stop 종료         | **PASS** |                |
| Redis 중복        | **PASS** |                |
| 안정성 테스트     | **PASS** |                |

---
<br>

## 🚨 이슈 기록
| 시간           | 증상           | 원인           | 조치           |
| :------------: | :------------: | :------------: | :------------: |
|                |                |                |                |
|                |                |                |                |

---
<br>

# 🏆 테스트 결론
**Collector 서비스 통합 테스트 결과**

---
## 1. 전체 안정성
- 서비스 기동, Stop 종료, Redis/Kafka 연동 등 모든 핵심 기능 정상 동작
- 장시간 실행 테스트에서 메모리 누수 및 프로세스 종료 없음
- 시스템 리소스 사용량 안정적
---
## 2. 성능 평가
- **CPU I/O Wait: 0.005% → 0.0286%**  
  → 증가 폭이 매우 작으며 **디스크 병목 없음**

- **CPU 사용률: 1% → 22.2%**  
  → 서비스 기동에 따른 정상적인 증가이며 **과부화 없음**

- **Load Average: 0.1 → 2.7**  
  → 작업 처리 증가에 따른 상승이나 **시스템 부하 정상 범위**

- **메모리 사용률: 34% → 37%**  
  → 사용량 변화가 미미하며 **메모리 누수 없음**

- **데이터 파이프라인 상태 (기동 후 확인)**
  - 크롤링 데이터 **정상 수집**
  - Redis **중복 필터 정상 동작**
  - Kafka **메시지 전송 정상**
---
## 3. 개선 필요 사항
- 테스트 중 발견된 이슈 없음 (**현재까지 모든 항목 PASS**)
---
