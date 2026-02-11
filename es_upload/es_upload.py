from conf.config_log import setup_logger
from common.job_class import Get_env, Get_properties, StopChecker
from common.postgres_hook import PostgresHook
from common.hdfs_hook import HdfsHook
from common.es_hook import ElasticsearchHook

import time, gzip, io, json
from elasticsearch import Elasticsearch, helpers

logger = setup_logger(__name__)

# ===============================
# Main 함수 (순차 처리)
# ===============================
def _main():
    try:
        # ===============================
        # 환경 변수 및 설정 로드
        # ===============================
        es_upload_env = Get_env._es_upload()
        pg_env = Get_env._postgres()
        hadoop_env = Get_env._hadoop()
        es_env = Get_env._es()
        properties = Get_properties(es_upload_env["config_path"])
        logger.info("환경 변수 및 설정 로드 완료")

        # ===============================
        # Postgresql 연결
        # ===============================
        postgresql = PostgresHook(
            pg_env["pg_host"],
            pg_env["pg_port"],
            pg_env["pg_db"],
            pg_env["pg_user"],
            pg_env["pg_password"]
        )
        postgresql.connect()
        logger.info("PostgreSQL 연결 완료")

        # ===============================
        # Hadoop 연결
        # ===============================
        hdfs = HdfsHook(
            host=hadoop_env["hadoop_fs_name"],
            user=hadoop_env["hadoop_user"]
        )
        hdfs.connect()
        logger.info("Hadoop 연결 완료")

        # ===============================
        # Elasticsearch 연결
        # ===============================
        es = ElasticsearchHook(
            hosts = es_env["es_host"].split(","),
            timeout = int(properties["es"]["timeout"])
        )
        es.connect()
        logger.info("Elasticsearch 연결 완료")

        # ===============================
        # 메인 처리 루프
        # ===============================
        cluster_num = int(properties["option"]["cluster_num"])
        process_num = int(properties["option"]["process_num"])

        while True:
            # ===============================
            # 종료 플래그 체크
            # ===============================
            if StopChecker._job_stop(es_upload_env["stop_dir"], es_upload_env["stop_file"]):
                logger.warning("Stop 파일 감지 → Es_upload 종료")
                break

            # 처리할 파일 정보 가져오기
            row = postgresql.fetchone(
                properties["sql"]["select_hadoop_new"],
                (cluster_num, process_num)
            )
            if not row:
                logger.info("처리할 대상 파일 없음, 대기 후 재시도..")
                time.sleep(30)
                continue

            file_path = row[0]
            txid = row[1]
            logger.info(f"==== Processing file: {file_path} (txid: {txid}) ====")

            # ===============================
            # HDFS 데이터 읽기 및 Elasticsearch 업로드
            # ===============================
            hdfs_file = hdfs.read_bytes(file_path)
            with gzip.GzipFile(fileobj=io.BytesIO(hdfs_file)) as gz:
                def _bulk_generator():
                    action = None
                    for line in gz:
                        line = line.strip()
                        doc = json.loads(line.decode("utf-8"))

                        if 'index' in doc: # 액션
                            action = doc["index"]
                        else: # 데이터
                            yield {
                                "_index": action["_index"],
                                "_id": action["_id"],
                                "_source": doc
                            }
                            action = None

                success, _ = es.bulk_upload(
                    actions = _bulk_generator(),
                    chunk_size = int(properties["es"]["chunk"])
                )

            # 처리 커밋
            postgresql.execute(
                properties["sql"]["update_hadoop_event"],
                (txid, file_path),
                commit=True
            )

            logger.info(f"==== Processing file: {file_path} → {es_env['job_index']} {success}건 처리")
            time.sleep(3)

    except Exception as e:
        logger.error("Es_upload 실행 중 오류 발생, 모든 배치 중단", exc_info=True)

    finally:
        postgresql.close()
        es.close()
        logger.info("프로세스 종료. 모든 자원 반납 완료")

if __name__ == "__main__":
    _main()
