#!/usr/bin/env bash
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

# Utility script to validate an instance before creating a compute resource AMI for AWS Batch to consume
# For more information, see http://docs.aws.amazon.com/batch/latest/userguide/compute_resource_AMIs.html.
# This script checks for the following conditions:
#  1) Docker installed, version 1.9 or greater
#  2) If ECS agent checkpoint file exists
#  3) If yum is installed, it checks for the ecs-init package
ECS_AGENT_CHECKPOINT_FILE=/var/lib/ecs/data/ecs_agent_data.json
DOCKER_MINIMUM_MAJOR_VERSION=1
DOCKER_MINIMUM_MINOR_VERSION=9
which docker > /dev/null 2>&1
if [ "$?" -ne 0 ]; then
    echo "Please install Docker version 1.9 or higher"
    exit -1;
fi

MAJORVERSION=`docker --version |awk '{print $3}' | awk -F "." '{print $1}'`
MINORVERSION=`docker --version |awk '{print $3}' | awk -F "." '{print $2}'`
if [ $MAJORVERSION -lt $DOCKER_MINIMUM_MAJOR_VERSION ]; then
    echo "ERROR: Please install Docker version 1.9 or higher"
fi
if [ $MAJORVERSION -eq $DOCKER_MINIMUM_MAJOR_VERSION ]; then
    if [ $MINORVERSION -lt $DOCKER_MINIMUM_MINOR_VERSION ];then
       echo "ERROR: Please install Docker version 1.9 or higher"
    fi
fi

if [ -s $ECS_AGENT_CHECKPOINT_FILE ]; then
   echo "ERROR: Please remove $ECS_AGENT_CHECKPOINT_FILE before creating the AMI"
   exit -1;
fi
which rpm > /dev/null 2>&1
if [ "$?" -eq 0 ]; then
  rpm -q $ECS_INIT_PACKAGE > /dev/null 2>&1
  if [ "$?" -ne 0 ]; then
     echo "Please install the ecs-init package for better support of your custom AMI in AWS Batch."
  fi
fi

echo "No issues detected with your instance."
echo "For more information, see http://docs.aws.amazon.com/batch/latest/userguide/compute_resource_AMIs.html."
echo "If you intend to apply IAM roles to your jobs for AWS permissions,"
echo "please run the following commands on your instance before creating your AMI."
echo "  sysctl -w net.ipv4.conf.all.route_localnet=1"
echo "  iptables -t nat -A PREROUTING -p tcp -d 169.254.170.2 --dport 80 -j DNAT --to-destination 127.0.0.1:51679"
echo "  iptables -t nat -A OUTPUT -d 169.254.170.2 -p tcp -m tcp --dport 80 -j REDIRECT --to-ports 51679"

