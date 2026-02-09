# 🚚 **hadoop_upload.service** - 통합 테스트
> Hadoop Upload 백그라운드 서비스의 **통합 테스트 문서**

---
<br>

## 🎯 테스트 목적
- **NFS NDJSON → 병합 → gzip 압축 → HDFS 업로드 전체 파이프라인 검증**
- LINE_LIMIT 기준 파일 병합 동작 확인
- 업로드 성공 시 NFS 원본 삭제 검증
- 업로드 실패 복구 로직 테스트
- Stop 파일 기반 안전 종료 검증
- 장시간 실행 안정성 확인

---
<br>

## 🧩 테스트 환경

| 항목 | 내용 |
|------|------|
| OS | Ubuntu 22.04 |
| Shell | Bash |
| Hadoop | HDFS 3.2.4 Cluster |
| NFS | `/nfs/job_data` |
| Grafana | 모니터링 활성 |

---
<br>

## ▶️ 사전 준비
```bash
# 서비스 상태 확인
sudo systemctl status hadoop_upload.service

# NFS 데이터 확인
ls -l /nfs/job_data

# HDFS 상태 확인
hdfs dfsadmin -report

# HDFS 업로드 경로 확인
hdfs dfs -ls /hdfs_tmp_data
```

---
<br>

# 🔍 테스트 시나리오
## **✅ 1. 서비스 정상 기동 테스트**
### ✔ 목적 : 서비스가 정상적으로 시작되고 루프 동작하는지 확인
---
### ✔ 절차
```bash
sudo systemctl start hadoop_upload.service
sudo systemctl status hadoop_upload.service
```
---
### **✔ 검증 항목 (정상 확인)**
✅ 서비스 상태: active (running)  
✅ 로그 파일 생성됨  
✅ while 루프 정상 동작  
✅ ERROR 로그 없음

---
<br>

## **✅ 2. NFS → 병합 → HDFS 업로드 테스트**
### ✔ 목적 : NDJSON 파일이 LINE_LIMIT 기준으로 병합 후 업로드 되는지 확인
---
### ✔ 절차
```bash
ls /nfs/job_data
hdfs dfs -ls /hdfs_tmp_data
```
---
### **✔ 검증 항목 (정상 확인)**

✅ NDJSON 라인 수 집계 정상  
✅ LINE_LIMIT(500) 기준 병합 수행  
✅ gzip 압축 파일 생성  
✅ HDFS 업로드 성공

---
<br>

## **✅ 3. 업로드 성공 후 원본 삭제 테스트**
### ✔ 목적 : HDFS 업로드 성공 시 NFS 원본 파일 삭제 확인
---
### **✔ 검증 항목 (정상 확인)**
✅ 업로드 완료 파일 삭제  
✅ 미처리 파일 유지  
✅ 로그에 삭제 기록 존재

---
<br>

## **✅ 4. 업로드 실패 복구 테스트**
### ✔ 목적 : 업로드 실패 시 정리 및 재시작 동작 확인
---
### **✔ 검증 항목 (정상 확인)**

✅ 실패 로그 기록  
✅ 로컬 압축 파일 미삭제  
✅ 재시작 루프 정상 유지  
✅ 서비스 중단 없음

---
<br>

## **✅ 5. Stop 파일 종료 테스트**
### ✔ 절차
```bash
touch /work/jsy/job_project/hadoop_upload/control/hadoop_upload.stop
```
---
### **✔ 검증 항목**
✅ Stop 파일 감지  
✅ 현재 작업 완료 후 종료  
✅ 서비스 정상 종료

---
<br>

## **✅ 6. 정합성 검증**
### ✔ 목적 : NFS 라인 수와 병합 업로드 결과 검증
---
### **✔ 검증 결과**
| 항목 | 결과 |
|------|------|
| 총 NDJSON 라인 수 | **34,109 라인** |
| 병합 기준 | **500 라인/파일** |
| 생성된 업로드 파일 수 | **69개** |
| 정합성 결과 | ✅ Good |

---
<br>

## 📊 리소스 모니터링 결과 (Grafana)
> Hadoop Upload 서비스 기동 전/후 비교

| 📌 지표 | 기동 전 | 기동 후 |
|--------|--------|--------|
| **CPU I/O Wait (iowait)** | 0.18% | **0.5%** |
| **CPU 사용률** | 0.5% | **3.5%** |
| **Load Average (1m)** | 0.1 | **0.5** |
| **메모리 사용률** | 39% | **41%** |

---
### ✔ 평가
✅ CPU/메모리 증가폭 낮음  
✅ I/O 부하 안정적  
✅ 시스템 전체 영향 미미

---
<br>

## 📜 로그 확인
```bash
tail -f /work/job_project/logs/hadoop_upload/*.log
```
---

### **✔ 검증 항목**
✅ INFO 로그 정상  
✅ ERROR 로그 없음  
✅ 업로드 기록 확인

---
<br>

## 📝 테스트 결과 기록

| 테스트 항목 | 결과 | 비고 |
|------------|------|------|
| 서비스 기동 | **PASS** | |
| 병합/업로드 | **PASS** | |
| 원본 삭제 | **PASS** | |
| 실패 복구 | **PASS** | |
| Stop 종료 | **PASS** | |
| 정합성 검증 | **PASS** | |
| 리소스 안정성 | **PASS** | |

---
<br>

# 🏆 테스트 결론 (요약)
**Hadoop upload 서비스 통합 테스트 결과**

---
## 1. 전체 안정성
- 34,109 라인을 500 단위로 병합하여 69개 파일 업로드 성공
- 업로드 및 삭제 로직 정상 동작
- Stop 종료 안정 처리
---
## 2. 성능 평가
- CPU/메모리 사용률 안정적
- I/O 부하 낮음
- 시스템 영향 최소
---
## 3. 개선 필요 사항
- 테스트 중 발견된 이슈 없음 (현재까지 모든 항목 PASS)
---
