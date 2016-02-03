#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Ansible module to manage vhosts on nine managed (v)servers
(c) 2016, Flavian Sierk <flavian.sierk@ibrows.ch>
"""

DOCUMENTATION = '''
---
module: nine-vhost
author: Flavian Sierk
version_added: "0.1"
short_description: Manage vhosts on nine managed servers
description:
    - Manages vhosts with nine-manage-vhosts
'''

import os
import pwd
import grp
import json
import platform

class NineVhost(object):
    platform = "Generic"
    distribution = None

    def __new__(cls, *args, **kwargs):
        return load_platform_subclass(NineVhost, args, kwargs)

    def __init__(self, ansible):
        self.ansible      = ansible
        self.domain       = ansible.params['domain']
        self.user         = ansible.params['user']
        self.state        = ansible.params['state']
        self.remove       = ansible.params['remove']
        self.rel_path     = ansible.params['rel_path']
        self.web_root     = ansible.params['web_root']
        self.template     = ansible.params['template']

    def execute_command(self, cmd):
        cmd.insert(0, 'sudo')
        return self.ansible.run_command(cmd, check_rc=True)


    def remove_vhost(self):
        cmd = [self.ansible.get_bin_path('nine-manage-vhosts', True)]
        cmd.append('virtual-host')
        cmd.append('remove')
        cmd.append(self.domain)

        return self.execute_command(cmd)

    def create_vhost(self):
        cmd = [self.ansible.get_bin_path('nine-manage-vhosts', True)]
        cmd.append('virtual-host')
        cmd.append('create')
        cmd.append(self.domain)

        if self.user is not None:
            cmd.append('--user=%s' % self.user)

        if self.rel_path is not None:
            cmd.append('--relative-path=%s' % self.rel_path)

        if self.web_root is not None:
            cmd.append('--webroot=%s' % self.web_root)

        if self.template is not None:
            cmd.append('--template=%s' % self.template)

        return self.execute_command(cmd)

    def modify_vhost(self):
        cmd = [self.ansible.get_bin_path('nine-manage-vhosts', True)]
        cmd.append('virtual-host')
        cmd.append('update')
        cmd.append(self.domain)

        if self.rel_path is not None:
            cmd.append('--relative-path=%s' % self.rel_path)

        if self.web_root is not None:
            cmd.append('--webroot=%s' % self.web_root)

        if self.template is not None:
            cmd.append('--template=%s' % self.template)

        return self.execute_command(cmd)

    def vhost_exists(self):
        vhosts = self.get_vhosts_list()
        for vhost in vhosts:
            if vhost["domain"] == self.domain:
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
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            domain=dict(required=True, aliases=['host'], type='str'),
            remove=dict(default='no', type='bool'),
            user=dict(default=None, type='str'),
            web_root=dict(default=None, type='str'),
            rel_path=dict(default=None, type='str'),
            template=dict(default=None, type='str'),
            # update_password=dict(default='always',choices=['always','on_create'],type='str')
        )
    )

    vhost = NineVhost(module)

    rc = None
    out = ''
    err = ''
    result = {}
    result['domain'] = vhost.domain
    result['state'] = vhost.state

    if vhost.state == 'absent':
        if vhost.vhost_exists():
            (rc, out, err) = vhost.remove_vhost()
            if rc != 0:
                module.fail_json(name=vhost.domain, msg=err, rc=rc)
            result['remove'] = vhost.remove
    elif vhost.state == 'present':
        if not vhost.vhost_exists():
            (rc, out, err) = vhost.create_vhost()
        # else:
            # (rc, out, err) = vhost.modify_vhost()
        if rc is not None and rc != 0:
            module.fail_json(name=vhost.domain, msg=err, rc=rc)

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
