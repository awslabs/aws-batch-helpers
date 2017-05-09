#
# Copyright 2013-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance with the
# License. A copy of the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "LICENSE.txt" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
# OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions and
# limitations under the License.
#
# Submits an image classification training job to an AWS Batch job queue, and tails the CloudWatch log output.
#

import argparse
import sys
import time
from datetime import datetime

import boto3
from botocore.compat import total_seconds

batch = boto3.client(
    service_name='batch',
    region_name='us-east-1',
    endpoint_url='https://batch.us-east-1.amazonaws.com')

cloudwatch = boto3.client(
    service_name='logs',
    region_name='us-east-1',
    endpoint_url='https://logs.us-east-1.amazonaws.com')

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument("--name", help="name of the job", type=str, default='train_rnn_mnist')
parser.add_argument("--job-queue", help="name of the job queue to submit this job", type=str, default='gpu_queue')
parser.add_argument("--job-definition", help="name of the job job definition", type=str, default='mxnet')
parser.add_argument("--command", help="command to run", type=str,
                    default='python /mxnet/example/image-classification/train_mnist.py --network lenet --gpus 0 --model-prefix /mnt/model/mnist')
parser.add_argument("--wait", help="block wait until the job completes", action='store_true')

args = parser.parse_args()

def printLogs(logGroupName, logStreamName, startTime):
    kwargs = {'logGroupName': logGroupName,
              'logStreamName': logStreamName,
              'startTime': startTime,
              'startFromHead': True}

    lastTimestamp = 0L
    while True:
        logEvents = cloudwatch.get_log_events(**kwargs)

        for event in logEvents['events']:
            lastTimestamp = event['timestamp']
            timestamp = datetime.utcfromtimestamp(lastTimestamp / 1000.0).isoformat()
            print '[%s] %s' % ((timestamp + ".000")[:23] + 'Z', event['message'])

        nextToken = logEvents['nextForwardToken']
        if nextToken and kwargs.get('nextToken') != nextToken:
            kwargs['nextToken'] = nextToken
        else:
            break
    return lastTimestamp


def getLogStream(logGroupName, jobName, jobId):
    response = cloudwatch.describe_log_streams(
        logGroupName=logGroupName,
        logStreamNamePrefix=jobName + '/' + jobId
    )
    logStreams = response['logStreams']
    if not logStreams:
        return ''
    else:
        return logStreams[0]['logStreamName']

def nowInMillis():
    endTime = long(total_seconds(datetime.utcnow() - datetime(1970, 1, 1))) * 1000L
    return endTime


def main():
    spin = ['-', '/', '|', '\\', '-', '/', '|', '\\']
    logGroupName = '/aws/batch/job'

    jobName = args.name
    jobQueue = args.job_queue
    jobDefinition = args.job_definition
    command = args.command.split()
    wait = args.wait

    submitJobResponse = batch.submit_job(
        jobName=jobName,
        jobQueue=jobQueue,
        jobDefinition=jobDefinition,
        containerOverrides={'command': command}
    )

    jobId = submitJobResponse['jobId']
    print 'Submitted job [%s - %s] to the job queue [%s]' % (jobName, jobId, jobQueue)

    spinner = 0
    running = False
    startTime = 0

    while wait:
        time.sleep(1)
        describeJobsResponse = batch.describe_jobs(jobs=[jobId])
        status = describeJobsResponse['jobs'][0]['status']
        if status == 'SUCCEEDED' or status == 'FAILED':
            print '%s' % ('=' * 80)
            print 'Job [%s - %s] %s' % (jobName, jobId, status)
            break
        elif status == 'RUNNING':
            logStreamName = getLogStream(logGroupName, jobName, jobId)
            if not running and logStreamName:
                running = True
                print '\rJob [%s - %s] is RUNNING.' % (jobName, jobId)
                print 'Output [%s]:\n %s' % (logStreamName, '=' * 80)
            if logStreamName:
                startTime = printLogs(logGroupName, logStreamName, startTime) + 1
        else:
            print '\rJob [%s - %s] is %-9s... %s' % (jobName, jobId, status, spin[spinner % len(spin)]),
            sys.stdout.flush()
            spinner += 1

if __name__ == "__main__":
    main()
