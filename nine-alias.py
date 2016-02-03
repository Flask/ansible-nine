#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Ansible module to manage vhost aliases on nine managed (v)servers
(c) 2016, Flavian Sierk <flavian.sierk@ibrows.ch>
"""

DOCUMENTATION = '''
---
module: nine-alias
author: Flavian Sierk
version_added: "0.1"
short_description: Manage nine vhosts aliases
description:
    - Create and deletes vhosts with nine-manage-vhosts
'''

import os
import pwd
import grp
import json
import platform

class NineAlias(object):
    platform = "Generic"
    distribution = None

    def __new__(cls, *args, **kwargs):
        return load_platform_subclass(NineAlias, args, kwargs)

    def __init__(self, ansible):
        self.ansible      = ansible
        self.domain       = ansible.params['domain']
        self.alias         = ansible.params['alias']
        self.state        = ansible.params['state']
        self.remove       = ansible.params['remove']

    def execute_command(self, cmd):
        cmd.insert(0, 'sudo')
        return self.ansible.run_command(cmd, check_rc=True)


    def remove_alias(self):
        cmd = [self.ansible.get_bin_path('nine-manage-vhosts', True)]
        cmd.append('alias')
        cmd.append('remove')
        cmd.append(self.alias)
        cmd.append('--virtual-host=%s' % self.domain)

        return self.execute_command(cmd)

    def create_alias(self):
        cmd = [self.ansible.get_bin_path('nine-manage-vhosts', True)]
        cmd.append('alias')
        cmd.append('create')
        cmd.append(self.alias)
        cmd.append('--virtual-host=%s' % self.domain)

        return self.execute_command(cmd)

    def alias_exists(self):
        vhosts = self.get_vhosts_list()
        for vhost in vhosts:
            if vhost["domain"] == self.domain:
                if self.alias in vhost['aliases']:
                    return True
        return False

    def get_vhosts_list(self):
        cmd = [self.ansible.get_bin_path('nine-manage-vhosts')]
        cmd.append('virtual-host')
        cmd.append('list')
        cmd.append('--json')

        (rc, out, err) = self.execute_command(cmd)
        return json.loads(out)

def main():

    module = AnsibleModule(
        argument_spec = dict(
            state   = dict(default='present', choices=['present', 'absent'], type='str'),
            domain  = dict(required=True, aliases=['host'], type='str'),
            alias   = dict(required=True, type='str'),
            remove  = dict(default='no', type='bool')
        )
    )

    alias = NineAlias(module)

    rc = None
    out = ''
    err = ''
    result = {}
    result['alias'] = alias.alias
    result['domain'] = alias.domain
    result['state'] = alias.state

    if alias.state == 'absent':
        if alias.alias_exists():
            (rc, out, err) = alias.remove_alias()
            if rc != 0:
                module.fail_json(name=alias.alias, msg=err, rc=rc)
            result['remove'] = alias.remove
    elif alias.state == 'present':
        if not alias.alias_exists():
            (rc, out, err) = alias.create_alias()
        if rc is not None and rc != 0:
            module.fail_json(name=alias.alias, msg=err, rc=rc)

    if rc is None:
        result['changed'] = False
    else:
        result['changed'] = True
    if out:
        result['stdout'] = out
    if err:
        result['stderr'] = err

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
main()
