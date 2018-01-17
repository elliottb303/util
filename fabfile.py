__author__ = 'ebmacbp'

from fabric.api import cd, env, run, task, puts, local, sudo
from whitelist import Whitelist
from fabric.contrib.files import exists
#external host data structure
from db_host_data import host_data

"""
Various fabric admin commands
"""
# env.hosts = []
repo = None

def repo_exists(repo):
    """
    :param repo: a repo name to verify
    :return: tru if repo already exists in the current directory when fabric is run; trigger remote git pull if not
    """
    return exists(repo)


def run_su(command, user="ec2-user"):
    """
    :param command: command to run on shell
    :param user: a user to switch to
    :return: Fabric runs the command remotely
    """
    return run('sudo su %s -c "%s"' % (user, command))

@task
def remote_whitelist(target_env, target_project, whitelist_type, sql_mode, ip_format, account_number, ip_or_regex=None, email=None):
    """
    :param target_env: stage or prod environment
    :param target_project: particular project
    :param ip_or_regex: and ip address, or regex string
    :param ip_format: a choice, ip or regex
    :param sql_mode: insert, or select
    :param account: account # to add
    :return: create a sql query file, and then use whitelist object to create a SQL login
    """
    w = Whitelist(target_env=target_env, target_project=target_project, whitelist_type=whitelist_type, ip_or_regex=ip_or_regex, ip_format=ip_format, sql_mode=sql_mode, email=email, account_number=account_number)

    # create sql file in working jenkins dir, then run ssh command.
    # running the ssh command locally instead of remote() b/c the ' < sqlfile ' insert process worked best
    w.setup()
    local(w.ssh_mysql_cmd())


@task
def remote_whitelist_jump(target_env, target_project, ip_or_regex, ip_format, sql_mode):
    """
    :param target_env: stage or prod environment
    :param target_project: particular project
    :param ip_or_regex: and ip address, or regex string
    :param ip_format: a choice, ip or regex
    :param sql_mode: insert, select
    :return: similar to remote_whitelist but created to hit jump first, pull down repo, then run remote command.
    this would be 2 jumps from Jenkins, not really any use case for this now
    """
    id = '/home/ec2-user/.ssh/id_rsa'
    # git clone to /tmp or user directory? will clone to tmp to keep things clean
    with cd('/tmp'):
        if repo_exists('scripts'):
            print 'repo exists, just update'
            with cd('scripts'):
                run('git pull')
        else:
            run('git clone ssh://git@%s' % repo)
        # run script remotely
        with cd('scripts'):
            # create sql file on dest host
            run('python whitelist.py %s %s %s %s %s' % (target_env, target_project, ip_or_regex, ip_format, sql_mode))

            # create whitelist object to return login to be used on dest host
            w = Whitelist(target_env=target_env, target_project=target_project, ip_or_regex=ip_or_regex, ip_format=ip_format, sql_mode=sql_mode)
            login_cmd = w.sql_login()
            host = host_data[target_env][target_project]['host']
            # print 'Will login to remote mysql with cmd:'
            # print login_cmd
            ssh_and_insert = 'ssh -o StrictHostKeyChecking=no -i %s %s %s < %s_%s_whitelist_%s.sql' % (id, host, login_cmd, target_env, target_project, sql_mode)
            # need to switch to ec2 user
            run_su(ssh_and_insert)


@task
def memory_usage():
    run('free -m')
