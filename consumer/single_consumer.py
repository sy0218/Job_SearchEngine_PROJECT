#!/usr/bin/python3
from conf.config_log import setup_logger
from common.job_class import Get_env, Get_properties, StopChecker, DataPreProcessor, CopyToLocal
from common.crawling_class import ChromeDriver, JobParser

from common.kafka_hook import KafkaHook

import sys, time
logger = setup_logger(__name__)

def _main():
    """
        카프카 컨슈머 &  채용공고 디테일 수집 로직
        - 웹 크롤링 → 제목 + 본문 추출 
    """

    def _get_xpaths(domain):
        """
        도메인별 XPath 정보 반환
        """
        return {
            "body": properties["xpath"][f"{domain}.body"],
            "banner": properties["xpath"][f"{domain}.banner"].split('|'),
            "wait": properties["xpath"][f"{domain}.wait"]
        }

    try:
        # ===============================
        # 환경 변수 및 설정 로드
        # ===============================
        consumer_env = Get_env._consumer()
        kafka_env = Get_env._kafka()
        properties = Get_properties(consumer_env["config_path"])

        logger.info("환경 변수 및 설정 로드 완료")

        # ===============================
        # Kafka + consumer + Schema Registry 연결
        # ===============================
        kafka = KafkaHook(kafka_env["kafka_host"])
        kafka.avro_consumer_connect(
            kafka_env["job_topic"], int(properties["partition_num"]["num"]),
            kafka_env["job_group_id"], kafka_env["schema_registry"]
        )
        logger.info("Kafka Avro Producer 연결 완료")

        # ===============================
        # Chrome 브라우저 기동
        # ===============================
        browser = ChromeDriver()
        logger.info("ChromeDriver 시작")

        # ===============================
        # 메인 컨슈머 & 채용공고 디테일 수집 로직
        # ===============================
        while True:
            batch = []

            while len(batch) != int(properties["poll_opt"]["poll_size"]):
                msg = kafka.poll(5.0)
                if msg is None:
                    logger.info(f"[INFO] 아직 메시지 없음!  현재 batch size: {len(batch)}.. 30초 대기..")
                    time.sleep(30)
                    continue

                batch.append(msg)

            offset_info = f"partition-{batch[0].partition()} : {batch[0].offset()} ~ {batch[-1].offset()}"
            logger.info(f"==== 배치 처리 시작.. {offset_info} ====")


            for batch_msg in batch:
                msg_value = batch_msg.value()
                print(msg_value)
                xpaths = _get_xpaths(msg_value["domain"])
                browser.get(msg_value["href"])
                browser.wait_css(xpaths["wait"], 20)

                parser = JobParser(browser)
                response = parser.get_response()

                # 텍스트 추출
                banner = parser.get_banner(xpaths["banner"], msg_value["domain"])
                body = parser.get_body(xpaths["body"])

                # 이미지 추출
                images_binary = parser.get_images(
                    xpaths["body"], msg_value["href"], 
                    int(properties["img_bypass"]["width"]),
                    int(properties["img_bypass"]["height"]),
                    int(properties["img_bypass"]["size"])
                )
                images = []
                for binary_blob, size_kb in images_binary:
                    img_hash = DataPreProcessor._hash(binary_blob.hex() + str(size_kb))
                    dir1 = img_hash[0] + img_hash[1]
                    dir2 = img_hash[2] + img_hash[3]

                    save_path = CopyToLocal.save(
                        (properties["img_path"]["dir"], dir1, dir2, img_hash),
                        binary_blob
                    )
                    images.append(save_path)

                batch_data = msg_value | {"body_text": body, "body_img": images} | banner
                print(batch_data)
                print()
             

            # kafka.commit(batch[-1]) # 컨슈머 커밋!
            logger.info(f"==== 배치 저장 성공.. {offset_info} ====")
            # ===============================
            # 종료 플래그 체크
            # ===============================
            if StopChecker._job_stop(
                consumer_env["stop_dir"],
                consumer_env["stop_file"]
            ):
                logger.warning("Stop 파일 감지 → Consumer 종료")
                break

            time.sleep(5)

    except Exception as e:
        logger.error("Consumer 실행 중 오류 발생", exc_info=True)
    finally:
        # ===============================
        # 리소스 정리
        # ===============================
        browser.quit()
        kafka.close()
        logger.info("Consumer 정상 종료")


if __name__ == "__main__":
    _main()
