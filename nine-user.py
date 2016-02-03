#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Ansible module to manage users on nine managed (v)servers
(c) 2016, Flavian Sierk <flavian.sierk@ibrows.ch>
"""

DOCUMENTATION = '''
---
module: nine-user
author: Flavian Sierk
version_added: "0.1"
short_description: Manage users on nine managed servers
description:
    - Manages users with nine-manage-vhosts
'''

import os
import pwd
import grp
import json
import platform

class NineUser(object):
    platform = "Generic"
    distribution = None

    def __new__(cls, *args, **kwargs):
        return load_platform_subclass(NineUser, args, kwargs)

    def __init__(self, ansible):
        self.ansible            = ansible
        self.name               = ansible.params['name']
        self.password           = ansible.params['password']
        self.remove             = ansible.params['remove']
        self.state              = ansible.params['state']
        self.update_password    = ansible.params['update_password']

    def execute_command(self, cmd):
        cmd.insert(0, 'sudo')
        return self.ansible.run_command(cmd, check_rc=True)

    def remove_user_userdel(self):
        cmd = [self.ansible.get_bin_path('nine-manage-vhosts', True)]
        cmd.append('user')
        cmd.append('remove')
        cmd.append(self.name)

        cmd.insert(0, 'sudo')

        return self.ansible.run_command(cmd, check_rc=True, data='Y')

    def create_user_useradd(self):
        cmd = [self.ansible.get_bin_path('nine-manage-vhosts', True)]
        cmd.append('user')
        cmd.append('create')
        cmd.append(self.name)

        if self.password is not None:
            cmd.append('--password=%s' % self.password)
        else:
            cmd.append('--no-password')

        return self.execute_command(cmd)

    def modify_user_usermod(self):
        cmd = [self.ansible.get_bin_path('nine-manage-vhosts', True)]
        cmd.append('user')
        cmd.append('update')
        cmd.append(self.name)

        if self.update_password == 'always' and self.password is not None:
            cmd.append('--password=%s' % self.password)

        return self.execute_command(cmd)

    def user_exists(self):

        users = self.get_user_list()
        for user in users:
            if user["name"] == self.name:
                return True
        return False

    def get_user_list(self):
        cmd = [self.ansible.get_bin_path('nine-manage-vhosts')]
        cmd.append('user')
        cmd.append('list')
        cmd.append('--json')

        (rc, out, err) = self.execute_command(cmd)
        return json.loads(out)

    def create_user(self):
        return self.create_user_useradd()

    def remove_user(self):
        return self.remove_user_userdel()

    def modify_user(self):
        return self.modify_user_usermod()

def main():

    module = AnsibleModule(
        argument_spec = dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            name=dict(required=True, aliases=['user'], type='str'),
            remove=dict(default='no', type='bool'),
            password=dict(default=None, type='str'),
            update_password=dict(default='always',choices=['always','on_create'],type='str')
        )
    )

    user = NineUser(module)

    rc = None
    out = ''
    err = ''
    result = {}
    result['name'] = user.name
    result['state'] = user.state

    if user.state == 'absent':
        if user.user_exists():
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err) = user.remove_user()
            if rc != 0:
                module.fail_json(name=user.name, msg=err, rc=rc)
            result['remove'] = user.remove
    elif user.state == 'present':
        if not user.user_exists():
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err) = user.create_user()
        else:
            (rc, out, err) = user.modify_user()
        if rc is not None and rc != 0:
            module.fail_json(name=user.name, msg=err, rc=rc)
        if user.password is not None:
            result['password'] = 'NOT_LOGGING_PASSWORD'

    if rc is None:
        result['changed'] = False
    else:
        result['changed'] = True
    if out:
        result['stdout'] = out
    if err:
        result['stderr'] = err

    # if user.user_exists():
    #     info = user.user_info()
    #     if info == False:
    #         result['msg'] = "failed to look up user name: %s" % user.name
    #         result['failed'] = True

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
main()
