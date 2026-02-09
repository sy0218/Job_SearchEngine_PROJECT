# 📦 **consumer.service** - 통합 테스트
> Consumer 데몬 서비스의 **통합 테스트 문서**

---
<br>

## 🎯 테스트 목적
- **Consumer 서비스의 전체 크롤링 파이프라인 검증**
- Kafka / NFS 연동 정상 여부 확인  
- Stop 제어 및 안정 종료 테스트
- 멀티프로세스 안정성 검증
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
| Kafka | broker: 3.6.2 |
| NFS | 마운트된 공유 스토리지 |
| Grafana | 모니터링 활성 |

---
<br>

## ▶️ 사전 준비
```bash
# 서비스 상태 확인
sudo systemctl status consumer.service

# Kafka 토픽 목록 확인
kafka-topics.sh --list --bootstrap-server <broker>

# NFS 접근 테스트
ls -l /nfs
```

---
<br>

# 🔍 테스트 시나리오
## **✅ 1. 서비스 정상 기동 테스트**
### ✔ 목적 : Consumer 서비스가 정상적으로 시작되는지 확인
---
### ✔ 절차
1) 서비스 시작
2) 로그 확인
3) 로그에서 오류 여부 확인
```bash
sudo systemctl start consumer.service
sudo systemctl status consumer.service
```
---
### **✔ 검증 항목 (정상 확인)**
✅ 서비스 상태: active (running)  
✅ ERROR 로그 없음  
✅ Kafka Consumer & Producer 정상 연결  
✅ 워커 프로세스(ChromeDriver) 정상 실행

---
<br>

## **✅ 2. Kafka 메시지 수신/처리 테스트**
### ✔ 목적 : Kafka로부터 정상적으로 메시지를 받아 처리하는지 확인
---
### ✔ 절차
1) Kafka에 테스트 job_header 메시지 생성
2) Consumer 로그 확인
3) NFS에 생성된 NDJSON / 이미지 저장 확인
---
### **✔ 검증 항목 (정상 확인)**
✅ Kafka 메시지 수신 성공  
✅ ChromeDriver로 페이지 접속 및 데이터 파싱 성공  
✅ NFS에 NDJSON 파일 생성  
✅ 이미지 바이너리 파일 생성

---
<br>

## **✅ 3. Stop 파일 종료 테스트**
### ✔ 목적 : Stop 파일 생성 시 Consumer가 안전하게 종료되는지 확인
---
### ✔ 절차
```bash
touch /work/job_project/consumer/control/consumer.stop
```
---
### **✔ 검증 항목 (정상 확인)**
✅ Stop 파일 감지 후 안전 종료  
✅ 워커 ChromeDriver 프로세스 종료  
✅ 로그에 Stop 처리 메시지 기록

---
<br>

## **✅ 4. 멀티프로세스 안정성 테스트**
### ✔ 목적 : 동시 다발적으로 배치 요청이 들어올 때 안정적으로 처리되는지 확인
---
### ✔ 절차
1) Kafka에 여러 메시지 일괄 전송
2) Consumer 병렬 처리 여부 확인
3) 결과 NFS 저장 및 OCR topic 전송 확인
---
### **✔ 검증 항목 (정상 확인)**

✅ poll_size 만큼 병렬 처리 수행  
✅ 각 워커 정상 종료 및 자원 반납  
✅ 메시지 처리 결과 정상 저장

---
<br>

## **✅ 5. NFS 저장 경로 테스트**
### ✔ 목적
NDJSON 및 이미지 저장 경로가 정상 동작하는지 확인
---
### ✔ 절차
1) 처리된 결과의 NFS 경로 확인
2) 이미지 해시 값과 실제 파일 매칭 확인
---
### **✔ 검증 항목 (정상 확인)**
✅ NDJSON 파일 정상 생성  
✅ 이미지 바이너리 각 경로에 정상 저장  
✅ 파일 권한/소유권 이상 없음

---
<br>

## **✅ 6. 장시간 실행 안정성 테스트**
### ✔ 목적 : 24시간 이상 실행 시도 및 자원 누수 여부 확인
---
### **✔ 검증 항목 (정상 확인)**
✅ 메모리 누수 없음  
✅ ChromeDriver 누적 프로세스 없음  
✅ Kafka & NFS 저장 정상 유지

---
<br>

## **✅7. 정합성 검증**
### ✔ 목적 : Kafka 토픽과 파싱된 데이터 수 비교로 처리 정합성 확인
---
### **✔ 검증 항목 (정상 확인)**
| 항목                   | 검증 방법 | 결과 |
|------------------------|----------|------|
| 총 처리해야 될 Kafka 토픽 갯수 | `kafka-run-class.sh kafka.tools.GetOffsetShell --bootstrap-server 192.168.122.60:9092 --topic job_header_topic --time -1` | 34,109 건 |
| 파싱된 데이터 수        | `wc -l *.ndjson \| awk 'END{print $1}'` | 34,109 건 |
| 정합성 결과             | Kafka 토픽 수와 NDJSON 수 비교 | ✅ Good (34,109 건 일치) |




---
<br>

## 📊 리소스 모니터링 예시 (Grafana)
> Consumer 서비스 기동 전/후 리소스 비교

| 📌 지표 | 📈 Grafana 쿼리 | 🔍 측정 결과 |
|--------|----------------|-------------|
| **CPU I/O Wait (iowait)** | `avg(rate(node_cpu_seconds_total{instance="192.168.122.65:9100", mode="iowait"}[1m])) * 100` | **0.01% (기동 전)** → **0.24% (기동 후)** |
| **CPU 사용률** | `100 - (avg(rate(node_cpu_seconds_total{instance="192.168.122.65:9100", mode="idle"}[1m])) * 100)` | **1.5% (기동 전)** → **30.3% (기동 후)** |
| **Load Average (1m)** | `node_load1{instance="192.168.122.65:9100"}` | **0.02 (기동 전)** → **4.9 (기동 후)** |
| **메모리 사용률** | `(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100` | **39% (기동 전)** → **43% (기동 후)** |

---
<br>

## 📜 로그 확인
```bash
tail -f /work/job_project/logs/consumer/*.log
```
---
### **✔ 검증 항목 (정상 확인)**
✅ ERROR 로그 없음  
✅ Kafka Consumer/Producer log 정상  
✅ 이미지 저장, NDJSON 저장 로그 확인

---
<br>

## 📝 테스트 결과 기록
| 테스트 항목               | 결과      | 비고          |
| :------------------------: | :------: | :------------ |
| 서비스 기동               | **PASS** |                |
| Kafka 메시지 처리         | **PASS** |                |
| Stop 파일 처리            | **PASS** |                |
| 멀티프로세스 처리        | **PASS** |                |
| NFS 저장                  | **PASS** |                |
| 장시간 안정성             | **PASS** |                |
| 정합성 검증             | **PASS** |                |

---
<br>

## 🚨 이슈 기록

| 시간           | 증상           | 원인           | 조치           |
| :------------: | :------------: | :------------: | :------------: |
| 2026-02-07     | 페이지를 찾을 수 없음 | 크롤링 대상 페이지 없음 | 명시적 예외 처리 추가 ✅ 적용완료 |
| 2026-02-07     | wait 메서드 실패 | Selenium wait 실패 | 재시도 로직 추가 ✅ 적용완료 |
| 2026-02-07     | 이미지 path 오류 | Invalid URL '//...' | `urljoin`로 절대 경로 처리 ✅ 적용완료 |
| 2026-02-08     | Docker 디스크 사용률 99% | Chrome 캐시 파일 누적 | Chrome 캐시 비활성화 옵션 추가, /tmp/.*Chrom* 정리 ✅ 적용완료 |
| 2026-02-08     | 이미지 다운로드 실패 (SSL 인증서) | SSL 인증서 검증 실패 | verify=False로 가능하나 보안 이슈로 현재 미적용 ⚠️ 검토중 |

---
<br>

# 🏆 테스트 결론 (요약)
**Consumer 서비스 통합 테스트 결과**

---
## 1. 전체 안정성
- Kafka 수신/처리, ChromeDriver, NFS 저장 등 모든 핵심 기능 정상 동작  
- 멀티프로세스 안정적 병렬 처리  
- Stop 파일에 따른 안전한 종료 정상 처리
- 테스트 중 발견된 페이지 없음 예외, wait retry, 이미지 path 오류, Docker 디스크 문제 등 모두 **적용 완료**
- 정합성 검증 결과 **Kafka 토픽 수와 NDJSON 수 일치**
---
## 2. 성능 평가
- CPU, Load, Memory 등 시스템 리소스 안정적 유지  
- ChromeDriver 누수 없음  
- Kafka 처리 지연 없음
- Grafana 모니터링 결과 CPU 사용률, I/O Wait, Load, 메모리 모두 정상 범위 유지
---
## 3. 개선 필요 사항
- 이미지 다운로드 SSL 인증서 문제는 **보안 고려로 현재 미적용, 검토중**
- 나머지 테스트 중 발견된 이슈는 모두 조치 완료 (현재까지 모든 항목 PASS)
---
