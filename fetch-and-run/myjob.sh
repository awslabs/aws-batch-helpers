#!/bin/bash

date
echo "Args: $@"
env
echo "This is my simple test job!."
echo "jobId: $AWS_BATCH_JOB_ID"
sleep $1
date
echo "bye bye!!"
