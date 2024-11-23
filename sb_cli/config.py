import os
from enum import Enum

API_BASE_URL = os.getenv("SWEBENCH_API_URL", "https://api.swebench.com")

class Subset(str, Enum):
    swe_bench_m = 'swe-bench-m'
    swe_bench_lite = 'swe-bench_lite'
