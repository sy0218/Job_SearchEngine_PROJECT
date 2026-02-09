#!/usr/bin/python3
import sys, time, atexit, os, psutil
from concurrent.futures import ProcessPoolExecutor, as_completed
from conf.config_log import setup_logger
from common.job_class import Get_env, Get_properties, StopChecker, DataPreProcessor, CopyToLocal
from common.crawling_class import ChromeDriver, JobParser
from common.kafka_hook import KafkaHook

from datetime import datetime

logger = setup_logger(__name__)

# ===============================
# 각 워커 프로세스의 독립적인 자원 풀
# ===============================
worker_context = {"browser": None, "properties": None, "nfs_img": None}

# ===============================
# 공통 자원 정리 ( 모든 Chrome/Driver 종료 )
# ===============================
def clean_all():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if ('chrome' in proc.info['name']) or ('chromedriver' in ' '.join(proc.info['cmdline'])):
                proc.kill()
        except psutil.NoSuchProcess:
            pass
    logger.info("모든 Chrome/Driver 종료 완료")

# ===============================
# 워커 초기화 : 워커 프로세스를 초기화하고 필요한 리소스 준비 
# ( 매번 객체 생성 오버헤드 피하기 위함 )
# ===============================
def init_worker(config_path, nfs_img_path):
    worker_context["properties"] = Get_properties(config_path)
    worker_context["nfs_img"] = nfs_img_path
    worker_context["browser"] = ChromeDriver()
    logger.info(f"Worker 초기화 성공 (PID: {os.getpid()})")

# ===============================
# 메시지 처리
# ( 실제 크롤링 및 데이터 가공 )
# ===============================
def process_message(msg_value):
    browser = worker_context["browser"]
    props = worker_context["properties"]
    nfs_img = worker_context["nfs_img"]

    try:
        domain = msg_value["domain"]
        xpaths = {
            "body": props["xpath"][f"{domain}.body"],
            "banner": props["xpath"][f"{domain}.banner"].split("|"),
            "wait": props["xpath"][f"{domain}.wait"]
        }

        browser.get(msg_value["href"])
        no_page = props["option"]["no_page_text"].split("|")
        if not browser.is_page_available(no_page):
            logger.warning(f"페이지 없음 → 메시지 건너뜀 (URL: {msg_value.get('href')})")
            return None
        browser.wait_css(xpaths["wait"], 10)

        # 사전 셋업 ( 필요한 도메인 작업 )
        setup_flag = props["option"][f"{domain}.setup_flag"]
        if setup_flag == 'y':
            browser.Jobplanet_Auto_Mation(props["auto_setup"][domain].split('\t'), 30)

        parser = JobParser(browser)
        parser.get_response()
        banner = parser.get_banner(xpaths["banner"], domain)
        body = parser.get_body(xpaths["body"])

        images_binary = parser.get_images(
            xpaths["body"], msg_value["href"],
            int(props["img_bypass"]["width"]),
            int(props["img_bypass"]["height"]),
            int(props["img_bypass"]["size"])
        )

        images = []
        for binary_blob, size_kb in images_binary:
            img_hash = DataPreProcessor._hash(binary_blob.hex() + str(size_kb))
            save_path = CopyToLocal.save(
                (nfs_img, img_hash[0:2], img_hash[2:4], img_hash),
                binary_blob
            )
            images.append(img_hash)

        return msg_value | {"body_text": body, "body_img": images} | banner

    except Exception as e:
        logger.error(f"메시지 처리 실패 (URL: {msg_value.get('href')}): {e}")
        raise

# ===============================
# Future 결과 수집
# ===============================
def collect_results(futures):
    results = []
    for future in as_completed(futures, timeout=600):
        res = future.result()
        if res is not None: # 페이지 없으면 수집 안 함
            results.append(res)
    return results

# ===============================
# Main 함수
# ===============================
def _main():
    # ===============================
    # 환경 변수 및 설정 로드
    # ===============================
    consumer_env = Get_env._consumer()
    kafka_env = Get_env._kafka()
    nfs_env = Get_env._nfs()
    properties = Get_properties(consumer_env["config_path"])
    poll_size = int(properties["poll_opt"]["poll_size"])
    logger.info("환경 변수 및 설정 로드 완료")

    # ===============================
    # Kafka + consumer + Schema Registry 연결
    # ===============================
    kafka_consumer = KafkaHook(kafka_env["kafka_host"])
    kafka_consumer.avro_consumer_connect(
        kafka_env["job_topic"], int(properties["partition_num"]["num"]),
        kafka_env["job_group_id"], kafka_env["schema_registry"]
    )
    logger.info("Kafka Avro Consumer 연결 완료")

    # ===============================
    # Kafka + producer 연결
    # ===============================
    kafka_producer = KafkaHook(kafka_env["kafka_host"])
    kafka_producer.producer_connect()  # 일반 Producer
    logger.info("Kafka Produce 연결 완료")

    try:
        # ===============================
        # [ 멀티프로세스 ]
        # ProcessPoolExecutor : 멀티 프로세스 관리자
        # → executor 이름 붙여서, 추후 관리자에게 일을 시킬 떄 executor.submit 사용
        #
        # max_workers = poll_size
        # → 일꾼( 프로세스 ) 몇 명이나 둘거임? → 여기서는 poll_size 만큼
        #
        # initializer = init_worker
        # → 일꾼 ( 프로세스 ) 일을 시작하기 전에 미리 교육함(초기화 ㅋㅋ)
        # → 크롬 객체 생성 오버헤드를 줄이기 위해 사용
        #
        # initargs=(c_env["config_path"],)
        # → init_worker 함수에 전달할 인자 ( 프로세스 환경 변수 셋팅 )  
        # ===============================
        with ProcessPoolExecutor(
            max_workers=poll_size,
            initializer=init_worker,
            initargs=(consumer_env["config_path"], nfs_env["nfs_img"])
        ) as executor:

            logger.info(f"Multi-Consumer 루프 시작 (Workers: {poll_size})")

            batch = []
            while True:
                # Stop file 체크
                if StopChecker._job_stop(consumer_env["stop_dir"], consumer_env["stop_file"]):
                    logger.warning("Stop 파일 감지 → 종료 프로세스 진입")
                    break

                while len(batch) < poll_size:
                    msg = kafka_consumer.poll(3.0)
                    if msg is None:
                        break
                    batch.append(msg)

                if len(batch) < poll_size:
                    logger.info(f"[INFO] 아직 메시지 없음!  현재 batch size: {len(batch)}.. 30초 대기..")
                    time.sleep(30)
                    continue

                offset_info = f"partition-{batch[0].partition()} : {batch[0].offset()} ~ {batch[-1].offset()}"
                logger.info(f"==== 배치 병렬 처리 시작.. {offset_info} ====")

                futures = [executor.submit(process_message, m.value()) for m in batch]
                futures_results = collect_results(futures)

                # body_img → ocr_img 토픽 전송
                for futures_result in futures_results:
                    for img_path in futures_result.get("body_img", []):
                        kafka_producer.produce(kafka_env["ocr_topic"], img_path)
                kafka_producer.flush()

                # ndjson 저장할 파일명
                ndjson_fn = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{properties['partition_num']['num']}.ndjson"
                # dict → NDJSON 변환
                ndjson_data = DataPreProcessor._dict_to_ndjson(futures_results)
                # ndjson 저장
                CopyToLocal.save((nfs_env["nfs_data"], ndjson_fn), ndjson_data.encode("utf-8"))

                # kafka 오프셋 커밋
                kafka_consumer.commit(batch[-1])
                batch = []
                logger.info(f"==== 배치 병렬 처리 완료.. {offset_info} ====")

                time.sleep(5)

    except Exception as e:
        logger.error("Consumer 실행 중 오류 발생, 모든 배치 중단", exc_info=True)

    finally:
        kafka_producer.flush()
        kafka_consumer.close()
        clean_all()
        time.sleep(3)
        os.system("rm -rf /tmp/.*Chrom*")
        logger.info("프로세스 종료. 모든 자원 반납 완료.")            


if __name__ == "__main__":
    _main()
