# 🕵️ **hadoop_event.service** - 통합 테스트
> HDFS CLOSE Event Watcher 데몬 서비스의 **통합 테스트 문서**

---
<br>

## 🎯 테스트 목적
- **HDFS CLOSE 이벤트 감시 파이프라인 전체 검증**
- HDFS → PostgreSQL 이벤트 적재 정상 여부 확인
- systemd 기반 서비스 기동/종료 안정성 검증
- 이벤트 누락 여부 및 정합성 확인
- 장시간 실행 안정성 테스트
- 시스템 리소스 사용량 모니터링

---
<br>

## 🧩 테스트 환경
| 항목 | 내용 |
|------|------|
| OS | Ubuntu 22.04 |
| Java | OpenJDK 11 |
| Hadoop | HDFS 3.2.4 Cluster |
| PostgreSQL | 14 |
| Grafana | 모니터링 활성 |

---
<br>

## ▶️ 사전 준비
```bash
# 서비스 상태 확인
sudo systemctl status hadoop_event.service

# HDFS 접근 확인
hdfs dfs -ls /hive/job_project

# PostgreSQL 접속 확인
./sql.sh "select 1;"
```

---
<br>

# 🔍 테스트 시나리오
## **✅ 1. 서비스 정상 기동 테스트**
### ✔ 목적 : hadoop_event 서비스가 정상적으로 시작되는지 확인
---
### ✔ 절차
```bash
sudo systemctl start hadoop_event.service
sudo systemctl status hadoop_event.service
```
---
### **✔ 검증 항목 (정상 확인)**
✅ 서비스 상태: active (running)  
✅ PostgreSQL 연결 성공 로그 확인  
✅ HDFS watcher 시작 로그 확인  
✅ ERROR 로그 없음

---
<br>

## **✅ 2. HDFS CLOSE 이벤트 감지 테스트**
### ✔ 목적 : HDFS 업로드 시 CLOSE 이벤트가 정상 감지되는지 확인
---
### ✔ 절차
```bash
hdfs dfs -put test.gz /hive/job_project/
```
---
### **✔ 검증 항목 (정상 확인)**
✅ CLOSE 이벤트 로그 기록  
✅ `_COPYING_` 제거 후 정상 경로 기록  
✅ PostgreSQL에 file_path / file_size INSERT 확인

---
<br>

## ✅ **3. PostgreSQL 적재 테스트**
### ✔ 목적 : 이벤트가 DB에 정상 저장되는지 검증
---
### ✔ 절차
```bash
./sql.sh "select * from job.hadoop_event order by id desc limit 5;"
```
---
### **✔ 검증 항목 (정상 확인)**
✅ 파일 경로 정확히 저장  
✅ 파일 크기 정확히 저장  
✅ 중복 이벤트 없음

---
<br>

## **✅ 4. 정합성 검증**

| 항목 | 검증 방법 | 결과 |
|------|----------|------|
| 총 입력 라인 수 | 34,109건 → 500라인 단위 분할 | 69개 파일 생성 |
| PostgreSQL 저장 건수 | `select count(*) from job.hadoop_event;` | **69건** |
| 정합성 결과 | HDFS 파일 수 vs DB 건수 비교 | ✅ Good (69건 일치) |

---
<br>

## **✅ 5. 서비스 종료 안정성 테스트**
### ✔ 목적 : SIGTERM 종료 시 안전하게 종료되는지 확인
---
### ✔ 절차
```bash
sudo systemctl stop hadoop_event.service
```
---
### **✔ 검증 항목 (정상 확인)**
✅ watcher 루프 정상 종료  
✅ PostgreSQL 연결 정상 해제  
✅ 로그 파일 정상 flush

---
<br>

## **✅ 6. 장시간 실행 안정성 테스트**
### **✔ 검증 항목 (정상 확인)**
✅ 이벤트 누락 없음  
✅ 로그 파일 정상 롤링  
✅ 메모리 누수 없음  
✅ 서비스 중단 없음

---
<br>

## 📊 리소스 모니터링 (Grafana)

| 📌 지표 | 📈 Grafana 쿼리 | 🔍 측정 결과 |
|--------|----------------|-------------|
| CPU I/O Wait | `avg(rate(node_cpu_seconds_total{mode="iowait"}[1m])) * 100` | **0.18% → 0.40%** |
| CPU 사용률 | `100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)` | **0.5% → 3.7%** |
| Load Average | `node_load1` | **0.1 → 0.3** |
| 메모리 사용률 | `(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100` | **39% → 41%** |

---
<br>

## 📜 로그 확인
```bash
tail -f /work/jsy/job_project/logs/hadoop_event/*.log
```
---
### **✔ 검증 항목 (정상 확인)**
✅ CLOSE 이벤트 로그 정상 기록  
✅ PostgreSQL INSERT 로그 확인  
✅ ERROR 로그 없음

---
<br>

## 📝 테스트 결과 기록

| 테스트 항목 | 결과 | 비고 |
|------------|------|------|
| 서비스 기동 | **PASS** | |
| HDFS 이벤트 감지 | **PASS** | |
| PostgreSQL 적재 | **PASS** | |
| 정합성 검증 | **PASS** | |
| 종료 안정성 | **PASS** | |
| 장시간 실행 | **PASS** | |

---
<br>

## 🚨 이슈 기록

| 시간 | 증상 | 원인 | 조치 |
|------|------|------|------|
| - | 없음 | - | 안정 동작 |

---
<br>

# 🏆 테스트 결론
**Hadoop event 서비스 통합 테스트 결과**

## 1. 전체 안정성
- HDFS CLOSE 이벤트 실시간 감시 정상 동작  
- PostgreSQL 적재 정확  
- systemd 기반 안정적 운영  
- 이벤트 누락 없음  
- 정합성 검증 결과 **69건 완전 일치**
---
## 2. 성능 평가
- CPU / Memory / I/O 모두 안정 범위  
- 장시간 실행 중 자원 누수 없음  
- Grafana 모니터링 결과 정상
---
## 3. 개선 필요 사항
- 테스트 중 발견된 이슈 없음 (현재까지 모든 항목 PASS)
---
