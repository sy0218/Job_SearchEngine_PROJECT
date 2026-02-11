# 📤 **es_upload.service** - 통합 테스트
> Elasticsearch 업로드 데몬 서비스의 **통합 테스트 문서**

---
<br>

## 🎯 테스트 목적
- **HDFS → Elasticsearch 업로드 파이프라인 검증**
- PostgreSQL 처리 상태 정합성 확인
- Elasticsearch 인덱싱 정상 여부 확인
- Stop 제어 및 안정 종료 테스트
- 병렬 처리(txid 기반) 안정성 검증
- 장시간 실행 안정성 검증
- 시스템 리소스 사용량 모니터링

---
<br>

## 🧩 테스트 환경
| 항목 | 내용 |
|------|------|
| OS | Ubuntu 22.04 |
| Python | 3.10 |
| Docker | 사용 |
| Elasticsearch | ES 8.4.2 Cluster |
| PostgreSQL | host: 14 |
| HDFS | HDFS 3.2.4 Cluster |
| Grafana | 모니터링 활성 |

---
<br>

## ▶️ 사전 준비
```bash
# 서비스 상태 확인
sudo systemctl status es_upload.service

# PostgreSQL 처리 상태 확인
./sql.sh "select count(*) from job.hadoop_new where event_check is True;"

# Elasticsearch 인덱스 확인
curl -X GET http://<es_host>:9200/_cat/indices?v
```

---
<br>

# 🔍 테스트 시나리오
## **✅ 1. 서비스 정상 기동 테스트**
### ✔ 목적 : es_upload 서비스가 정상적으로 시작되는지 확인
---
### ✔ 절차
```bash
sudo systemctl start es_upload.service
sudo systemctl status es_upload.service
```
---
### **✔ 검증 항목 (정상 확인)**
✅ 서비스 상태: active (running)  
✅ HDFS / PostgreSQL / Elasticsearch 연결 성공    
✅ ERROR 로그 없음  

---
<br>

## **✅ 2. Elasticsearch 업로드 테스트**
### ✔ 목적 : HDFS 파일이 Elasticsearch로 정상 업로드되는지 확인
---
### ✔ 절차
1) 업로드 대상 파일 처리 대기 상태 확인
2) es_upload 로그 확인
3) Elasticsearch 인덱스 문서 수 확인
---
### **✔ 검증 항목 (정상 확인)**
| 항목                  | 검증 방법                                                            | 결과              |
| ------------------- | ---------------------------------------------------------------- | --------------- |
| PostgreSQL 처리 완료 건수 | `select count(*) from job.hadoop_new where event_check is True;` | **69 건**        |
| Elasticsearch 문서 수  | `_cat/indices` 조회                                                | **34,109 docs** |
| 인덱스 상태              | health status 확인                                                 | ✅ green         |

---
<br>

## **✅ 3. Stop 파일 종료 테스트**
### ✔ 목적 : Stop 파일 생성 시 서비스가 안전 종료되는지 확인
---
### ✔ 절차
```bash
touch /work/job_project/es_upload/control/es_upload.stop
```
---
### **✔ 검증 항목 (정상 확인)**
✅ Stop 파일 감지 후 안전 종료  
✅ 처리 중이던 Chunk 정상 마무리    
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
### ✔ 목적 : PostgreSQL 처리 상태와 Elasticsearch 인덱스 정합성 확인
---
### **✔ 검증 항목 (정상 확인)**
| 항목                   | 검증 방법             | 결과           |
| -------------------- | ----------------- | ------------ |
| DB 처리 완료 건수          | Hadoop 이벤트 테이블 조회 | **69 건**     |
| Elasticsearch 인덱스 상태 | `_cat/indices` 조회 | ✅ green      |
| 총 문서 수               | docs.count 확인     | **34,109 건** |

---
<br>

## **✅ 6. 장시간 실행 안정성 테스트**
### ✔ 목적 : 장시간 실행 시 안정성 및 누수 여부 확인
---
### **✔ 검증 항목 (정상 확인)**
✅ 메모리 누수 없음    
✅ 업로드 중단/지연 없음    
✅ Elasticsearch 연결 안정 유지  

---
<br>

## 📊 리소스 모니터링 (Grafana)
> es_upload 서비스 기동 전/후 리소스 비교

| 📌 지표 | 📈 Grafana 쿼리 | 🔍 측정 결과 |
|--------|----------------|-------------|
| **CPU I/O Wait (iowait)** | `avg(rate(node_cpu_seconds_total{mode="iowait"}[1m])) * 100` | **0.005% (기동 전)** → **0.0045% (기동 후)** |
| **CPU 사용률** | `100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)` | **0.5% (기동 전)** → **23.3% (기동 후)** |
| **Load Average (1m)** | `node_load1` | **0.1 (기동 전)** → **1.13 (기동 후)** |
| **메모리 사용률** | `(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100` | **38.1% (기동 전)** → **38.5% (기동 후)** |

---
<br>

## 📜 로그 확인
```bash
tail -f /work/job_project/logs/es_upload/*.log
```
---
### **✔ 검증 항목 (정상 확인)**
✅ Elasticsearch Bulk 업로드 로그 정상  
✅ DB 커밋 로그 확인  
✅ ERROR 로그 없음  

---
<br>

## 📝 테스트 결과 기록
|       테스트 항목      |    결과    |  비고 |
| :---------------: | :------: | :-: |
|       서비스 기동      | **PASS** |     |
| Elasticsearch 업로드 | **PASS** |     |
|     Stop 파일 처리    | **PASS** |     |
|  병렬 처리 안정성 | **PASS** |    |
|       정합성 검증      | **PASS** |     |
|      장시간 안정성      | **PASS** |     |

---
<br>

## 🚨 이슈 기록
|  시간 |    증상   |  원인 |   조치  |
| :-: | :-----: | :-: | :---: |
|  -  | 특이사항 없음 |  -  | 정상 운영 |

---
<br>

# 🏆 테스트 결론
**es_upload 서비스 통합 테스트 결과**

---
## 1. 전체 안정성
- HDFS → Elasticsearch 업로드 정상 동작  
- 병렬 처리 환경에서도 충돌 없이 안정적 수행  
- PostgreSQL 처리 상태 정확히 반영
- Stop 파일 기반 안전 종료 정상 동작  
- 정합성 검증 결과 **DB와 Elasticsearch 일치**
---
## 2. 성능 평가
- CPU 및 Load 증가 있으나 정상 범위  
- 메모리 사용량 안정적 유지  
- Elasticsearch Bulk 업로드 성능 양호
---
## 3. 개선 필요 사항
- 테스트 중 발견된 이슈 없음 (현재까지 모든 항목 PASS)

---
