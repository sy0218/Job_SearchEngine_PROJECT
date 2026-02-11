# 🛢️ **warehouse.service** - 통합 테스트
> Warehouse 데몬 서비스의 **통합 테스트 문서**

---

<br>

## 🎯 테스트 목적
- **Warehouse 서비스의 전체 데이터 병합/처리 파이프라인 검증**
- HDFS / Redis / PostgreSQL 연동 정상 여부 확인
- OCR 병합 및 형태소 분석 처리 검증
- Stop 제어 및 안정 종료 테스트
- 병렬 처리(txid 기반) 안정성 검증
- 시스템 리소스 사용량 모니터링

---
<br>

## 🧩 테스트 환경
| 항목 | 내용 |
|------|------|
| OS | Ubuntu 22.04 |
| Python | 3.10 |
| Docker | 사용 |
| Hadoop | HDFS 3.2.4 Cluster |
| PostgreSQL | host: 14 |
| Redis | host: 7.4.7 |
| Elasticsearch | ES 8.4.2 Cluster |
| Grafana | 모니터링 활성 |

---
<br>

## ▶️ 사전 준비
```bash
# 서비스 상태 확인
sudo systemctl status warehouse.service

# HDFS 파일 확인
hdfs dfs -ls /hive/job_project/org
hdfs dfs -ls /hive/job_project/new

# PostgreSQL 상태 확인
./sql.sh "select count(*) from job.hadoop_event;"
```

---
<br>

# 🔍 테스트 시나리오
## **✅ 1. 서비스 정상 기동 테스트**
### ✔ 목적 : Warehouse 서비스가 정상적으로 시작되는지 확인
---
### ✔ 절차
```bash
sudo systemctl start warehouse.service
sudo systemctl status warehouse.service
```
---
### **✔ 검증 항목 (정상 확인)**
✅ 서비스 상태: active (running)  
✅ Redis / PostgreSQL / HDFS 연결 성공    
✅ 형태소 분석기 초기화 성공  
✅ ERROR 로그 없음  

---
<br>

## **✅ 2. HDFS → OCR 병합 처리 테스트**
### ✔ 목적 : 원본 데이터와 OCR 데이터가 정상 병합되는지 확인
---
### ✔ 절차
1) HDFS org 파일 처리 로그 확인
2) Redis OCR 데이터 병합 여부 확인
3) hadoop new 디렉토리 gzip 생성 확인
---
### **✔ 검증 항목 (정상 확인)**
✅ gzip NDJSON 정상 읽기  
✅ OCR 결과 정상 병합    
✅ Elasticsearch Bulk 포맷 생성 성공  
✅ new 경로에 gzip 파일 생성  

---
<br>

## **✅ 3. Stop 파일 종료 테스트**
### ✔ 목적 : Stop 파일 생성 시 안전 종료 확인
---
### ✔ 절차
```bash
touch /work/job_project/warehouse/control/warehouse.stop
```
---
### **✔ 검증 항목 (정상 확인)**
✅ Stop 파일 감지 후 안전 종료  
✅ 처리 중인 배치 정상 종료    
✅ 로그에 종료 메시지 기록   

---
<br>

## **✅ 4. 병렬 처리 안정성 테스트**
### ✔ 목적 : txid 기반 병렬 처리 정상 동작 확인
---
### ✔ 절차
1) cluster_num / process_num 설정 후 동시 실행
2) 각 노드 처리 로그 비교
---
### **✔ 검증 항목 (정상 확인)**
✅ txid 분산 처리 충돌 없음  
✅ 중복 처리 없음   
✅ 처리 누락 없음   

---
<br>

## **✅ 5. 정합성 검증**
### ✔ 목적 : 원본 데이터와 결과 데이터 개수 비교
---
### **✔ 검증 결과 (정상 확인)**
| 항목            | 검증 방법                                                              | 결과              |
| ------------- | ------------------------------------------------------------------ | --------------- |
| 처리 대기 이벤트 수   | `select count(*) from job.hadoop_event where event_check is null;` | 69              |
| 처리 완료 이벤트 수   | `select count(*) from job.hadoop_event where event_check is True;` | 69              |
| HDFS org 파일 수 | `/hive/job_project/org/*.gz`                                       | 69              |
| HDFS new 파일 수 | `/hive/job_project/new/*.gz`                                       | 69              |
| **정합성 결과**        | **org == new == DB**                                                   | ✅ **Good (69건 일치)** |

---
<br>

## 📊 리소스 모니터링 (Grafana)
> Warehouse 서비스 기동 전/후 리소스 비교

| 📌 지표 | 📈 Grafana 쿼리 | 🔍 측정 결과 |
|--------|----------------|-------------|
| **CPU I/O Wait (iowait)** | `avg(rate(node_cpu_seconds_total{mode="iowait"}[1m])) * 100` | **0.003% (기동 전)** → **0.02% (기동 후)** |
| **CPU 사용률** | `100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)` | **0.8% (기동 전)** → **13.5% (기동 후)** |
| **Load Average (1m)** | `node_load1` | **0.2 (기동 전)** → **0.89 (기동 후)** |
| **메모리 사용률** | `(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100` | **38.2% (기동 전)** → **39.3% (기동 후)** |

---
<br>

## 📜 로그 확인
```bash
tail -f /work/job_project/logs/warehouse/*.log
```
---
### **✔ 검증 항목 (정상 확인)**
✅ ERROR 로그 없음  
✅ HDFS 처리 로그 정상  
✅ OCR 병합 로그 정상  
✅ DB 커밋 로그 확인  

---
<br>

## 📝 테스트 결과 기록
|   테스트 항목   |    결과    | 비고 |
| :--------: | :------: | :- |
|   서비스 기동   | **PASS** |    |
|  OCR 병합 처리 | **PASS** |    |
| Stop 파일 처리 | **PASS** |    |
|  병렬 처리 안정성 | **PASS** |    |
|   정합성 검증   | **PASS** |    |
|   성능 테스트   | **PASS** |    |

---
<br>

## 🚨 이슈 기록
|  시간 |    증상   |  원인 |   조치  |
| :-: | :-----: | :-: | :---: |
|  -  | 특이사항 없음 |  -  | 정상 운영 |

---
<br>

# 🏆 테스트 결론
**Warehouse 서비스 통합 테스트 결과**

---
## 1. 전체 안정성
- HDFS → OCR 병합 → 형태소 분석 → HDFS 적재까지 전체 파이프라인 정상 동작  
- 병렬 처리 환경에서도 충돌 없이 안정적 수행  
- Stop 파일 기반 안전 종료 정상 동작  
- 정합성 검증 결과 **org / new / DB 데이터 완전 일치**
---
## 2. 성능 평가
- CPU / Memory / I/O 모두 안정 범위 유지  
- 대용량 gzip 처리에도 병목 없음  
- Grafana 기준 리소스 사용량 정상
---
## 3. 개선 필요 사항
- 테스트 중 발견된 이슈 없음 (현재까지 모든 항목 PASS)

---
