# 📝 **Project Overview**
- **프로젝트 이름:** 채용 공고 **검색엔진**  
- **설명:** 여러 채용 플랫폼에 **분산된 채용공고 데이터를** 실시간으로 수집하여, 검색엔진, 유사도 분석, 기업 요약 기능을 제공함으로써 취업 준비생들의 수고를 줄여주는 프로젝트입니다.
- **목표:**  
  1. 구인·구직 사이트로부터 채용공고 데이터를 안정적이고 빠르게 수집  
  2. Kafka, Redis, Hadoop, Elasticsearch 기반의 준실시간 데이터 파이프라인 구축  
  3. **OCR** 및 텍스트 정제를 통해 데이터 활용도 극대화  
  4. LLM과 형태소 분석을 활용한 **고차원적 정보** 제공
---
<br><br>

# 🛠️ **Trouble Shooting**
- ✅ **Ansible 자동화 도입! 다중 서버 환경 구성 & 환경 구축 시간 폭발적 단축!** → **[`📘 정리 문서`](./docs/ansible.md)**
- ✅ **Redis 캐시 활용! 대규모 조회/삽입 효율 극대화 & 서버 부하 최소화!** → **[`📘 정리 문서`](./docs/redis.md)**
- ✅ **Kafka Avro 직렬화 적용! 디스크/네트워크 효율 향상 & 토픽 용량 절감!** → **[`📘 정리 문서`](./docs/kafka_avro.md)**
- ✅ **디테일 크롤링 멀티프로세스 + 브라우저 객체 재사용 + Scale-Up/Scale-Out 적용! 크롤링 속도 약 10초 → 1초, 50,00건 처리 138시간 → 4.6시간 수준으로 개선!** → **[`📘 정리 문서`](./docs/crawling_scaleup_scaleout.md)**
- ✅ **채용공고 이미지 다수로 OCR 불가피! EasyOCR 정확도 확보 + 단건 처리 & Scale-Out 전략으로 시스템 부하 최소화!** → **[`📘 정리 문서`](./docs/easyocr_tess.md)**
---
<br><br>

# 🧰 **Project Operations Manual**
- 여기서는 **서비스 운영 및 관리를 위해 필요한 환경 구축과 설정 매뉴얼**을 제공합니다.  
> 🚀 **Ansible로 자동화된 환경 설정 예시**는 🔗 [`Ansible 레포지토리`](https://github.com/sy0218/Ansible-Multi-Server-Setup)에서 확인하세요!

| **서비스** | **설명** | **매뉴얼** |
|------------|----------|------------|
| 🖲️ **KVM 기반 Ubuntu 서버 설치** | KVM 가상화 서버 설치 및 초기 설정 | **[`📘 매뉴얼`](./docs/kvm_setup.md)** |
| ⏰ **클러스터 시간 & 클럭 동기화** | 클러스터 서버 시간과 클럭 초기 설정 | **[`📘 매뉴얼`](./docs/sync_time_clock.md)** |
| 📷 **다중 서버 모니터링** | Prometheus · Grafana 기반 통합 모니터링 구성 | **[`📘 매뉴얼`](./docs/prometheus_grafana_setup.md)** |
| 🌐 **Ubuntu Chrome & WebDriver 설치** | 웹 수집용 Chrome과 드라이버 설치 | **[`📘 매뉴얼`](./docs/ubuntu_chrome_webdriver_install.md)** | 
| 📂 **NFS 서버 & 클라이언트 구축** | NFS 공유 디렉토리 및 마운트 설정 | **[`📘 매뉴얼`](./docs/nfs_setup.md)** |
| 🐳 **Docker 환경 구축** | 컨테이너 개발/운영 환경 설정 | **[`📘 매뉴얼`](./docs/docker_setup.md)** |
| 💾 **PostgreSQL DB** | 설치 및 초기 데이터베이스 설정 | **[`📘 매뉴얼`](./docs/postgresql_setup.md)** |
| ⚡ **Redis 캐시** | 고속 데이터 처리용 Redis 설정/운영 | **[`📘 매뉴얼`](./docs/redis_setup.md)** |
| 🦓 **ZooKeeper** | 분산 환경 설정 관리 및 동기화 | **[`📘 매뉴얼`](./docs/zookeeper_setup.md)** |
| 📡 **Kafka** | 데이터 스트리밍 플랫폼 구축/활용 | **[`📘 매뉴얼`](./docs/kafka_setup.md)** |
| └─ 📦 Schema Registry | 카프카 직렬화 & 스키마 관리 | **[`📘 매뉴얼`](./docs/kafka_schema_registry_setup.md)** |
| 🐘 **Hadoop** | 분산 시스템 클러스터 설치/설정 | **[`📘 매뉴얼`](./docs/hadoop_setup.md)** |
| 🐝 **Hive** | 데이터 웨어하우스 설치/운영 | **[`📘 매뉴얼`](./job_all_md/hive_manual.md)** |
| 🔍 **Elasticsearch** | 검색엔진 클러스터 설치/설정 | **[`📘 매뉴얼`](./docs/elasticsearch_setup.md)** |

---
<br><br>

# 🏎️ **Real-time Data Pipeline**
여기서는 **Kafka, Redis, Hadoop, Elasticsearch** 등을 활용해 구축한 **준실시간 데이터 파이프라인**의 **수집·처리·적재·검색** 전체 흐름을 단계별로 문서화했습니다.

| **카테고리** | **서비스** | **설명** |
|--------------|------------|----------|
| **수집** | 📡 `collector.service` | 채용공고 **헤더 수집** → **[`📘 collector`](./docs/collector_service.md)** |
| **처리** | 📦 `consumer.service` | 채용공고 헤더 **데이터 소비 및 상세 저장** → **[`📘 consumer`](./docs/consumer_service.md)** |
| **처리** | 🚚 `hadoop_upload.service` | 로컬(NFS) 데이터 병합 후 **HDFS 업로드** → **[`📘 hadoop_upload`](./docs/hadoop_upload_service.md)** |
| **처리** | 🕵️ `hadoop_event.service` | HDFS CLOSE 이벤트 감시 → 로그 기록 → **PGSQL 적재**→ **[`📘 hadoop_event`](./docs/hadoop_event_service.md)** |
| **처리** | 🔍  `ocr.service` | Kafka 이미지 메타 수신 → Redis 캐싱 → **OCR 처리** → **[`📘 ocr_service`](./docs/ocr_service.md)** |
| **처리** | 🛢️ `warehouse.service` | **OCR 수신** → 텍스트 정제 + 형태소 분석 → ES 벌크용 전처리 → **HDFS 업로드**  → **[`📘 warehouse`](./docs/warehouse_service.md)** |
| **적재·검색** | 📤 `esupload.service` | HDFS Bulk 데이터 **Elasticsearch 전송** → **[`📘 esupload`](./job_all_md/esupload.md)** |

---
<br><br>


## 🛠️ **Tech Stack**

| Category | Stack |
|:--------:|:-----|
| 💻 **프로그래밍 언어** | ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=Python&logoColor=white) ![Shell Script](https://img.shields.io/badge/Shell%20Script-4EAA25?style=for-the-badge&logo=GNU%20Bash&logoColor=white) ![Java](https://img.shields.io/badge/Java-007396?style=for-the-badge&logo=Java&logoColor=white) |
| ☁️ **인프라 & 가상화** | ![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=Linux&logoColor=black) ![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=Docker&logoColor=white) ![KVM](https://img.shields.io/badge/KVM-FF6600?style=for-the-badge&logo=Linux&logoColor=white) |
| 🗄  **빅데이터 & 저장소** | ![Hadoop](https://img.shields.io/badge/Apache%20Hadoop-66CCFF?style=for-the-badge&logo=Apache%20Hadoop&logoColor=black) ![Hive](https://img.shields.io/badge/Apache%20Hive-FDEE21?style=for-the-badge&logo=Apache%20Hive&logoColor=black) ![Elasticsearch](https://img.shields.io/badge/Elasticsearch-005571?style=for-the-badge&logo=Elasticsearch&logoColor=white) |
| ⚡ **메시징 & 캐시** | ![Kafka](https://img.shields.io/badge/Apache%20Kafka-231F20?style=for-the-badge&logo=Apache%20Kafka&logoColor=white) ![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=Redis&logoColor=white) |
| 🌍 **웹 크롤링** | ![Selenium](https://img.shields.io/badge/Selenium-43B02A?style=for-the-badge&logo=Selenium&logoColor=white) ![Scrapy](https://img.shields.io/badge/Scrapy-9E1510?style=for-the-badge&logo=Scrapy&logoColor=white) |
| 🖼️  **OCR** | ![EasyOCR](https://img.shields.io/badge/EasyOCR-FF9900?style=for-the-badge&logo=python&logoColor=white) |
| 🤖 **AI / LLM** | ![LLM](https://img.shields.io/badge/LLM-FF6F61?style=for-the-badge&logo=OpenAI&logoColor=white) |
| 📊 **모니터링 도구** | ![Prometheus](https://img.shields.io/badge/Prometheus-263238?style=for-the-badge&logo=Prometheus&logoColor=white) ![Grafana](https://img.shields.io/badge/Grafana-F46800?style=for-the-badge&logo=Grafana&logoColor=white) |

---
