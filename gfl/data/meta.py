#  Copyright 2020 The GFL Authors. All Rights Reserved.
#  #
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#  #
#      http://www.apache.org/licenses/LICENSE-2.0
#  #
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

__all__ = [
    "JobMeta",
    "DatasetMeta"
]

from dataclasses import dataclass
from typing import List


@dataclass()
class Metadata:

    id: str = None
    owner: str = None
    create_time: int = None
    content: str = None


@dataclass()
class JobMeta(Metadata):

    datasets: List[str] = None


@dataclass()
class DatasetMeta(Metadata):

    size: int = 0
    used_cnt: int = 0