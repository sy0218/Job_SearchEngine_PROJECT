from conf.config_log import setup_logger
from common.job_class import Get_env, Get_properties, StopChecker, DataPreProcessor
from common.redis_hook import RedisHook
from common.postgres_hook import PostgresHook
from common.hdfs_hook import HdfsHook
from common.morph_analyzer import MorphAnalyzer
import time, json

logger = setup_logger(__name__)

# ===============================
# Main 함수 (순차 처리)
# ===============================
def _main():
    try:
        # ===============================
        # 환경 변수 및 설정 로드
        # ===============================
        warehouse_env = Get_env._warehouse()
        redis_env = Get_env._redis()
        pg_env = Get_env._postgres()
        hadoop_env = Get_env._hadoop()
        es_env = Get_env._es()
        properties = Get_properties(warehouse_env["config_path"])
        logger.info("환경 변수 및 설정 로드 완료")

        # ===============================
        # Redis 연결
        # ===============================
        redis = RedisHook(
            redis_env["redis_host"],
            redis_env["redis_port"],
            redis_env["redis_img_db"],
            redis_env["redis_password"],
            decode_responses=True
        )
        redis.connect()
        logger.info("Redis 연결 완료")

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
        # 형태소 분석 연결
        # ===============================
        morph = MorphAnalyzer()
        logger.info("Morph 연결 완료")

        # ===============================
        # 메인 처리 루프
        # ===============================
        cluster_num = int(properties["option"]["cluster_num"])
        process_num = int(properties["option"]["process_num"])

        while True:
            es_bulk = [] # 엘라스틱서치 bulk 용 리스트

            # ===============================
            # 종료 플래그 체크
            # ===============================
            if StopChecker._job_stop(warehouse_env["stop_dir"], warehouse_env["stop_file"]):
                logger.warning("Stop 파일 감지 → Warehouse 종료")
                break

            # 하둡에서 데이터 가져오는 로직
            row = postgresql.fetchone(
                properties["sql"]["select_hadoop_org"],
                (cluster_num, process_num)
            )

            if not row:
                logger.info("처리할 대상 파일 없음, 대기 후 재시도..")
                time.sleep(30)
                continue

            file_path = row[0]
            txid = row[1]

            logger.info(f"==== Processing file: {file_path} (txid: {txid}) ====")
            data = hdfs.read_bytes(file_path)

            text = DataPreProcessor._decompress_gzip_bytes(data)

            # 레디스에서 OCR 텍스트 가져오는 로직
            img_key = []
            job_json = []
            for line in text.splitlines():
                json_line = json.loads(line)
                job_json.append(json_line)
                img_key += json_line["body_img"]

            redis_pipe = redis.pipeline()
            for key in img_key:
                redis_pipe.exists(key)
            result = redis_pipe.execute()

            if result and not all(result):
                logger.info("이미지 OCR 준비중, 대기 후 재시도..")
                time.sleep(30)
                continue

            values = redis.mget(img_key)
            clean_texts = DataPreProcessor._clean_ocr_text(values)
            img_text_mapping = dict(zip(img_key, clean_texts))

            # 본문 텍스트 + OCR 텍스트 → 형태소 분석
            for idx in range(len(job_json)):
                ocr_texts = []
                for img_hash in job_json[idx]["body_img"]:
                    if img_text_mapping[img_hash]: # 이미지 텍스트가 존재시
                        ocr_texts.append(img_text_mapping[img_hash])
                if ocr_texts: # 병합할 이미지 테스트가 존재시
                    job_json[idx]["body_text"] += " ".join(ocr_texts)

                # 본문 텍스트 형태소 분석
                tokens = morph.analyze(job_json[idx]["body_text"])
                job_json[idx]["morph"] = tokens
                del job_json[idx]["body_img"]

                action_line = DataPreProcessor._get_es_action(es_env["job_index"], job_json[idx]["msgid"])
                doc_line = json.dumps(job_json[idx], ensure_ascii=False)
                es_bulk.append(action_line)
                es_bulk.append(doc_line)


            # 벌크용 최종 하둡에 gz으로 올리기
            hdfs_path = f"{properties['dir']['hadoop_dir']}/es_bulk_{time.strftime('%Y%m%d%H%M%S')}.gz"
            hdfs.upload_lines(hdfs_path, es_bulk)

            # 처리 커밋
            postgresql.execute(
                properties["sql"]["update_hadoop_event"],
                (txid, file_path),
                commit=True
            )

            logger.info(f"==== Processing file: {file_path} → {hdfs_path} ====")

            time.sleep(3)

    except Exception as e:
        logger.error(f"Warehouse 실행 중 오류 발생, 모든 배치 중단", exc_info=True)

    finally:
        redis.close()
        postgresql.close()
        logger.info("프로세스 종료. 모든 자원 반납 완료.")

if __name__ == "__main__":
    _main()
