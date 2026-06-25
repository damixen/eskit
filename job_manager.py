from pathlib import Path
import json

from job import ESKitJob
from executers import ESKitExecutor
from typing import List, Dict

__job_manager = None


# singleton
def init(cache_dir):
    global __job_manager
    __job_manager = ESKitJobManager(cache_dir)


def get():
    return __job_manager


class ESKitJobManager:

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.jobs_dir = cache_dir / "jobs"

    def submit(self, job: ESKitJob, executor: ESKitExecutor):
        """Start a job using the appropriate executor."""

        cache_path = f"{self.jobs_dir}/{job.id}.json"
        job.cache_path = cache_path

        log_path = f"{self.jobs_dir}/{job.id}.log"
        job.log_path = log_path
        # print(f"start executor:{job}")
        executor.start(job)

        self.save(job)

        return job

    def refresh(self, job: ESKitJob, executor: ESKitExecutor):
        """Refresh the current status of a job."""

        executor.refresh(job)

        self.save(job)

        return job

    def cancel(self, job: ESKitJob, executor: ESKitExecutor):
        executor.cancel(job)

        self.save(job)

    def save(self, job: ESKitJob):
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        with open(job.cache_path, "w") as fp:
            json.dump(job.to_dict(), fp, indent=2)

    def load(self, job_id: str) -> ESKitJob:
        path = self.jobs_dir / f"{job_id}.json"

        with open(path) as fp:
            data = json.load(fp)

        return ESKitJob.from_dict(data)

    def load_dict(self, host, job_id: str) -> Dict:
        host_cache_path = self.cache_dir / host / "cache" / "jobs" / f"{job_id}.json"
        local_cache_path = self.jobs_dir / f"{job_id}.json"

        path = None

        if Path(host_cache_path).exists():
            path = host_cache_path
        elif Path(local_cache_path).exists():
            path = local_cache_path

        if not path:
            print(f"job:{job_id} is not found.")
            return

        with open(path) as fp:
            data = json.load(fp)

        return data

    def list(self, host, local):
        jobs = []
        jobs_dir = self.jobs_dir
        if host:
            jobs_dir = self.cache_dir / host / "cache" / "jobs"
        print(f"jobs_dir:{jobs_dir}")

        for file in sorted(jobs_dir.glob("*.json")):
            with open(file) as fp:
                try:
                    jobs.append(ESKitJob.from_dict(json.load(fp)))
                except Exception as e:
                    print(e)

        if local:
            for file in sorted(self.jobs_dir.glob("*.json")):
                with open(file) as fp:
                    jobs.append(ESKitJob.from_dict(json.load(fp)))
        return jobs

    def list_dicts(self, host, local) -> List[Dict]:
        return [j.to_dict() for j in self.list(host, local)]
