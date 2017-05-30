# Licensed to Cloudera, Inc. under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  Cloudera, Inc. licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import absolute_import

import boto.utils
from boto.regioninfo import get_regions
from boto.s3.connection import Location

from django.utils.translation import ugettext_lazy as _

from desktop.lib.conf import Config, UnspecifiedConfigSection, ConfigSection, coerce_bool, coerce_password_from_script

from hadoop.core_site import get_s3a_access_key, get_s3a_secret_key


DEFAULT_CALLING_FORMAT='boto.s3.connection.OrdinaryCallingFormat'


def get_default_access_key_id():
  """
  Attempt to set AWS access key ID from script, else core-site, else None
  """
  access_key_id_script = AWS_ACCOUNTS['default'].ACCESS_KEY_ID_SCRIPT.get()
  return access_key_id_script or get_s3a_access_key()


def get_default_secret_key():
  """
  Attempt to set AWS secret key from script, else core-site, else None
  """
  secret_access_key_script = AWS_ACCOUNTS['default'].SECRET_ACCESS_KEY_SCRIPT.get()
  return secret_access_key_script or get_s3a_secret_key()


def get_default_region():
  return AWS_ACCOUNTS['default'].REGION.get() if 'default' in AWS_ACCOUNTS else Location.DEFAULT


AWS_ACCOUNTS = UnspecifiedConfigSection(
  'aws_accounts',
  help=_('One entry for each AWS account'),
  each=ConfigSection(
    help=_('Information about single AWS account'),
    members=dict(
      ACCESS_KEY_ID=Config(
        key='access_key_id',
        type=str,
        private=True,
        dynamic_default=get_default_access_key_id
      ),
      ACCESS_KEY_ID_SCRIPT=Config(
        key='access_key_id_script',
        default=None,
        private=True,
        type=coerce_password_from_script,
        help=_("Execute this script to produce the AWS access key ID.")),
      SECRET_ACCESS_KEY=Config(
        key='secret_access_key',
        type=str,
        private=True,
        dynamic_default=get_default_secret_key
      ),
      SECRET_ACCESS_KEY_SCRIPT=Config(
        key='secret_access_key_script',
        default=None,
        private=True,
        type=coerce_password_from_script,
        help=_("Execute this script to produce the AWS secret access key.")
      ),
      SECURITY_TOKEN=Config(
        key='security_token',
        type=str,
        private=True,
      ),
      ALLOW_ENVIRONMENT_CREDENTIALS=Config(
        help=_('Allow to use environment sources of credentials (environment variables, EC2 profile).'),
        key='allow_environment_credentials',
        default=True,
        type=coerce_bool
      ),
      REGION=Config(
        key='region',
        default=None,
        type=str
      ),
      HOST=Config(
        help=_('Alternate address for the S3 endpoint.'),
        key='host',
        default=None,
        type=str
      ),
      PROXY_ADDRESS=Config(
        help=_('Proxy address to use for the S3 connection.'),
        key='proxy_address',
        default=None,
        type=str
      ),
      PROXY_PORT=Config(
        help=_('Proxy port to use for the S3 connection.'),
        key='proxy_port',
        default=8080,
        type=int
      ),
      PROXY_USER=Config(
        help=_('Proxy user to use for the S3 connection.'),
        key='proxy_user',
        default=None,
        type=str
      ),
      PROXY_PASS=Config(
        help=_('Proxy password to use for the S3 connection.'),
        key='proxy_pass',
        default=None,
        type=str
      ),
      CALLING_FORMAT=Config(
        key='calling_format',
        default=DEFAULT_CALLING_FORMAT,
        type=str
      ),
      IS_SECURE=Config(
        key='is_secure',
        default=True,
        type=coerce_bool
      )
    )
  )
)


def is_enabled():
  return ('default' in AWS_ACCOUNTS.keys() and AWS_ACCOUNTS['default'].get_raw() and AWS_ACCOUNTS['default'].ACCESS_KEY_ID.get() is not None) or has_iam_metadata()


def has_iam_metadata():
  metadata = boto.utils.get_instance_metadata(timeout=1, num_retries=1)
  return 'iam' in metadata


def has_s3_access(user):
  return user.is_authenticated() and user.is_active and (user.is_superuser or user.has_hue_permission(action="s3_access", app="filebrowser"))


def config_validator(user):
  res = []

  if is_enabled():
    regions = get_regions('s3')
    region_names = [r.name for r in regions]

    for name in AWS_ACCOUNTS.keys():
      region_name = AWS_ACCOUNTS[name].REGION.get()
      if region_name not in region_names:
        res.append(('aws.aws_accounts.%s.region' % name, 'Unknown region %s' % region_name))

  return res
