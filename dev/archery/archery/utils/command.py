# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import os
import shutil
import subprocess

from .logger import logger, ctx


def find_exec(executable):
    exec_exists = os.path.exists(executable)
    executable = executable if exec_exists else shutil.which(executable)

    if executable is None:
        raise FileNotFoundError(executable)

    return executable


def default_bin(name, env, default):
    return name if name else os.environ.get(env, default)


# Decorator running a command and returning stdout
class capture_stdout:
    def __init__(self, strip=False, listify=False):
        self.strip = strip
        self.listify = listify

    def __call__(self, f):
        def strip_it(x):
            return x.strip() if self.strip else x

        def list_it(x):
            return x.decode('utf-8').splitlines() if self.listify else x

        def wrapper(*argv, **kwargs):
            # Ensure stdout is captured
            kwargs["stdout"] = subprocess.PIPE
            return list_it(strip_it(f(*argv, **kwargs).stdout))
        return wrapper


class Command:
    """ A runnable command.

    Class inheriting from the Command class must provide the bin
    property/attribute.
    """

    def run(self, *argv, **kwargs):
        assert(hasattr(self, "bin"))
        invocation = [find_exec(self.bin)]
        invocation.extend(argv)

        for key in ["stdout", "stderr"]:
            # Preserve caller intention, otherwise silence
            if key not in kwargs and ctx.quiet:
                kwargs[key] = subprocess.PIPE

        # Prefer safe by default
        if "check" not in kwargs:
            kwargs["check"] = True

        logger.debug(f"Executing `{invocation}`")
        return subprocess.run(invocation, **kwargs)

    def __call__(self, *argv, **kwargs):
        return self.run(*argv, **kwargs)


class CommandStackMixin:
    def run(self, *argv, **kwargs):
        stacked_args = self.argv + argv
        return super(CommandStackMixin, self).run(*stacked_args, **kwargs)


class Bash(Command):
    def __init__(self, bash_bin=None):
        self.bin = default_bin(bash_bin, "BASH", "bash")
