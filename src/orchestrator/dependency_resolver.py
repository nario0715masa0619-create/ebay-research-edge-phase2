from typing import List, Dict, Set
from .models import JobDefinition

class JobDependencyResolver:
    def resolve_execution_order(self, jobs: List[JobDefinition]) -> List[JobDefinition]:
        """
        Performs a topological sort on the provided jobs based on depends_on.
        """
        job_map = {j.job_name: j for j in jobs}
        visited: Set[str] = set()
        stack: List[str] = []
        permanent_marks: Set[str] = set()
        temporary_marks: Set[str] = set()

        def visit(job_name: str):
            if job_name in permanent_marks:
                return
            if job_name in temporary_marks:
                raise ValueError(f"Circular dependency detected involving job '{job_name}'.")

            temporary_marks.add(job_name)
            
            job = job_map.get(job_name)
            if job:
                # We only resolve dependencies within the provided subset of jobs
                # or assume dependencies outside are already satisfied or ignored
                for dep in job.depends_on:
                    if dep in job_map:
                        visit(dep)

            temporary_marks.remove(job_name)
            permanent_marks.add(job_name)
            stack.append(job_name)

        for job in jobs:
            visit(job.job_name)

        # The stack currently has jobs in 'leaf-first' order
        return [job_map[name] for name in stack]

    def get_independent_jobs(self, jobs: List[JobDefinition]) -> List[JobDefinition]:
        """Returns jobs that have no dependencies within the provided list."""
        return [j for j in jobs if not any(dep in [oj.job_name for oj in jobs] for dep in j.depends_on)]
