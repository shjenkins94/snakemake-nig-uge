#!/usr/bin/env python
"""
qsub-submit.py

Script to wrap qsub command (no sync) for Snakemake. Uses the following job or
cluster parameters:

+ `threads`
+ `resources`
    - `mem_gb`: Expected memory requirements in megabytes. Overrides
      cluster.mem_gb
"""

import os
import re
import sys  # for command-line arguments (get jobscript)
import subprocess
from pathlib import Path  # for path manipulation
from snakemake.utils import read_job_properties  # get info from jobscript


# Create a job name. Defaults to group name, then rule plus wildcards
def get_job_name(job: dict) -> str:
    if job.get("type", "") == "group":
        groupid = job.get("groupid", "group")
        jobid = job.get("jobid", "").split("-")[0]
        jobname = "{groupid}_{jobid}".format(groupid=groupid, jobid=jobid)
    else:
        wildcards = job.get("wildcards", {})
        wildcards_str = ("_".join(wildcards.values()) or "unique")
        name = job.get("rule", "") or "rule"
        jobname = "smk.{0}.{1}".format(name, wildcards_str)
    return jobname


# get the resources part of the command
def generate_resources_command(job: dict) -> str:
    # get values
    threads = job.get("threads", 1)
    resources = job.get("resources", {})
    # start by requesting threads in smp if threads > 1
    if threads > 1:
        thread_cmd = "-pe smp {threads}"
    else:
        thread_cmd = ""
    mem_gb = resources.get("mem_gb", int({{cookiecutter.default_mem_gb}}))
    mem_cmd = "-l s_vmem={mem_gb}G -l mem_req={mem_gb}G".format(mem_gb=mem_gb)
    if (threads >= int({{cookiecutter.reserve_min_threads}}) or
            mem_gb >= int({{cookiecutter.reserve_min_mem_gb}})):
        reserve_cmd = "-R yes"
    else:
        reserve_cmd = ""
    res_cmd = "{thread_cmd} {mem_cmd} {reserve_cmd}".format(
        thread_cmd=thread_cmd,
        mem_cmd=mem_cmd,
        reserve_cmd=reserve_cmd)
    return (res_cmd)


def get_log_files(jobname: str) -> str:
    # get the name of the job
    jobname = get_job_name(job)
    # determine names to pass through for job name, logfiles
    log_dir = "{{cookiecutter.default_cluster_logdir}}"
    # get the output file name
    out_log = "{}.out".format(jobname)
    err_log = "{}.err".format(jobname)
    # get logfile paths
    out_log_path = str(Path(log_dir).joinpath(out_log))
    err_log_path = str(Path(log_dir).joinpath(err_log))
    log_cmd = "-o {out} -e {err} -N {name}".format(
        out=out_log_path,
        err=err_log_path,
        name=jobname
    )
    return(log_cmd)


# get the jobscript (last argument)
jobscript = sys.argv[-1]

# read the jobscript and get job properties
job = read_job_properties(jobscript)

# get command to do cluster command (no sync)
submit_cmd = "qsub -terse -cwd -V"

# get queue part of command (if empty, don't put in anything)
queue_cmd = "-q {queue}" if "{{cookiecutter.default_queue}}" else ""

# get resources
res_cmd = generate_resources_command(job)

# get logs
log_cmd = get_log_files(job)

# get cluster commands to pass through, if any
cluster_cmd = " ".join(sys.argv[1:-1])

# format command
cmd = "{submit} {queue} {res} {log} {cluster} {jobscript}".format(
    submit=submit_cmd,
    queue=queue_cmd,
    res=res_cmd,
    log=log_cmd,
    cluster=cluster_cmd,
    jobscript=jobscript
)

proc = subprocess.run(cmd, check=True, shell=True, encoding='utf-8',
                      stdout=subprocess.PIPE)

print(proc.stdout.strip())



# proc = subprocess.run(command, stdout=subprocess.PIPE, check=True,
#                       encoding='utf-8')
# print(proc.stdout.strip())


# # run commands
# shell_stdout = shell(
#     # qsub submit command
#     submit_cmd
#     # specify required threads/resources
#     + " " + resources_cmd
#     # specify job name, output/error logfiles
#     + " " + jobinfo_cmd
#     # specify queue
#     + " " + queue_cmd
#     # put in pass-through commands
#     + " " + cluster_cmd
#     # finally, the jobscript
#     + " {jobscript}",
#     read=True  # get byte string from stdout
# )
# 
# # obtain job id from this, and print
# print(shell_stdout.decode().strip())