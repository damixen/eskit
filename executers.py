from job import ESKitJob
import subprocess
import os


class ESKitExecutor:
    def start(self, job):
        raise NotImplementedError

    def refresh(self, job):
        raise NotImplementedError

    def cancel(self, job):
        raise NotImplementedError


class LocalExecutor(ESKitExecutor):

    def start(self, job: ESKitJob):

        log_file = open(job.log_path, "ab")

        proc = subprocess.Popen(
            job.payload["cmd"], stdout=log_file, stderr=subprocess.STDOUT
        )

        job.pid = proc.pid
        job.status = "running"

        return proc


class RsyncExecutor(LocalExecutor):

    def start(self, job: ESKitJob):

        super().start(job)


class ElasticsearchExecutor(ESKitExecutor):
    def start(self, job):
        # Submit async request
        # task_id = submit_reindex(job.payload)

        # job.payload["task_id"] = task_id
        # job.status = "running"
        pass

    def refresh(self, job):
        # task = get_task(job.payload["task_id"])

        # if task["completed"]:
        #    job.status = "success"
        #    job.result = task
        # else:
        #    job.status = "running"
        pass

    def cancel(self, job):
        # cancel_task(job.payload["task_id"])
        pass
