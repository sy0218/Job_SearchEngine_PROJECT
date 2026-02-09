#!/usr/bin/bash

# load env
. /work/job_project/conf/job.conf
#exec python3 -u ${CONSUMER_WORK_DIR}/test.py
exec python3 -u ${CONSUMER_WORK_DIR}/wanted.py
#exec python3 -u ${CONSUMER_WORK_DIR}/consumer.py
