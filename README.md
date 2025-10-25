<a href="https://coraza.io/">
<img src="https://owasp.org/www-project-developer-guide/assets/images/logos/coraza.png" alt="Coraza WAF Logo" width="600"/>
</a>

# Ansible Role - Coraza WAF HAProxy Integration (SPOA)

Role to deploy the [Coraza WAF (OWASP)](https://coraza.io/) [HAProxy SPOA-integration](https://github.com/corazawaf/coraza-spoa) with its [Core-Ruleset](https://github.com/corazawaf/coraza-coreruleset).

We focus on the HAProxy community-edition as the enterprise-edition already has a built-in WAF!

[![Lint](https://github.com/O-X-L/ansible-role-haproxy-waf-coraza/actions/workflows/lint.yml/badge.svg)](https://github.com/O-X-L/ansible-role-haproxy-waf-coraza/actions/workflows/lint.yml)
[![Ansible Galaxy](https://badges.oss.oxl.app/galaxy.badge.svg)](https://galaxy.ansible.com/ui/standalone/roles/oxlorg/haproxy_waf_coraza)

**Molecule Integration-Tests**:

* Status: [![Molecule Test Status](https://badges.oss.oxl.app/haproxy_waf_coraza.molecule.svg)](https://github.com/O-X-L/ansible-role-oxl-cicd/blob/latest/templates/usr/local/bin/cicd/molecule.sh.j2) |
[![Functional-Tests](https://github.com/O-X-L/ansible-role-haproxy-waf-coraza/actions/workflows/integration_test_result.yml/badge.svg)](https://github.com/O-X-L/ansible-role-haproxy-waf-coraza/actions/workflows/integration_test_result.yml)
* Logs: [API](https://ci.oss.oxl.app/api/job/ansible-test-molecule-haproxy_waf_coraza/logs?token=2b7bba30-9a37-4b57-be8a-99e23016ce70&lines=1000) | [Short](https://badges.oss.oxl.app/log/molecule_haproxy_waf_coraza_test_short.log) | [Full](https://badges.oss.oxl.app/log/molecule_haproxy_waf_coraza_test.log)

Internal CI: [Tester Role](https://github.com/O-X-L/ansible-role-oxl-cicd) | [Jobs API](https://github.com/O-X-L/github-self-hosted-jobs-systemd)


**Tested:**
* Debian 12

----

## Install

```bash
# latest
ansible-galaxy role install git+https://github.com/O-X-L/ansible-role-haproxy-waf-coraza

# from galaxy
ansible-galaxy install oxlorg.haproxy_waf_coraza

# or to custom role-path
ansible-galaxy install oxlorg.haproxy_waf_coraza --roles-path ./roles
```

----

## Usage

### Example

Here you can find a detailed config example and its results:

* [Example](https://github.com/O-X-L/ansible-role-haproxy-waf-coraza/blob/latest/Example.md)

### Config

**Example**

```yaml
waf:
  apps:
    - name: 'default'
      block: false

    - name: 'default_block'
      block: true

    - name: 'be_app1'
      block: true

      rules:
        # override vars inside CoreRuleset config REQUEST-901-INITIALIZATION.conf
        vars:
          tx.allowed_methods: 'GET HEAD POST PUT DELETE OPTIONS'

        rule_changes:
          # disable PHP-checks
          'REQUEST-933-APPLICATION-ATTACK-PHP.conf': false

          # re-enable it
          # 'REQUEST-933-APPLICATION-ATTACK-PHP.conf': true

          # change/update single rules
          'REQUEST-944-APPLICATION-ATTACK-JAVA.conf':
            # disable (comment-out) single rule
            944100: false

            # re-enable it
            # 944100: true
                        
            # replace a rule with custom content
            944140: |
              SecRule ... \
                  "id:944140, ..."

```

----

### HAProxy Integration

Then you will need to include the SPOE-backend: `/etc/haproxy/waf-coraza.cfg`

And target the SPOE-agents in your HAProxy config: (or use the role [O-X-L/ansible-role-haproxy](https://github.com/O-X-L/ansible-role-haproxy) with `haproxy.waf.coraza.enable=true`)

```
http-request set-var(txn.waf_app) str(app1) if { req.hdr(host) -i -m str oxl.at test.oxl.at }

# fallback app
http-request set-var(txn.waf_app) str(default) if !{ var(txn.waf_app) -m found }

filter spoe engine coraza config /etc/haproxy/waf-coraza-spoe.cfg
http-request send-spoe-group coraza coraza-req
```

To log related information in HAProxy: (*after the send-spoe-group line*)

```
http-request capture var(txn.waf_app) len 50
http-request capture var(txn.coraza.id) len 16
http-request capture var(txn.coraza.error) len 1
http-request capture var(txn.coraza.action) len 8
```

And then perform the result-actions:

```
# deny or silent-drop:
http-request deny status 403 if { var(txn.coraza.action) -m str deny }
http-response deny status 403 if { var(txn.coraza.action) -m str deny }

http-request silent-drop if { var(txn.coraza.action) -m str drop }
http-response silent-drop if { var(txn.coraza.action) -m str drop }

# optional - redirect:
http-request redirect code 302 location %[var(txn.coraza.data)] if { var(txn.coraza.action) -m str redirect }
http-response redirect code 302 location %[var(txn.coraza.data)] if { var(txn.coraza.action) -m str redirect }
```

----

### Result

```bash
tree /etc/coraza-spoa -L 4
> ├── apps
> │   ├── be_app1
> │   │   └── v4.7.0
> │   │       ├── @crs-setup.conf
> │   │       ├── main.conf
> │   │       └── @owasp_crs
> │   ├── default
> │   │   └── v4.7.0
> │   │       ├── @crs-setup.conf
> │   │       ├── main.conf
> │   │       └── @owasp_crs
> │   ├── default_block
> │   │   └── v4.7.0
> │   │       ├── @crs-setup.conf
> │   │       ├── main.conf
> │   │       └── @owasp_crs
> │   └── _tmpl
> │       └── v4.7.0
> │           └── ...
> └── spoa.yml

# haproxy spoe backend: /etc/haproxy/waf-coraza.cfg
# haproxy spoe agents: /etc/haproxy/waf-coraza-spoe.cfg

cat /etc/haproxy/waf-coraza-spoe.cfg 
> [coraza]
> spoe-agent coraza-agent
>     messages    coraza-req
>     option      var-prefix      coraza
>     option      set-on-error    error
>     timeout     hello           2s
>     timeout     idle            2m
>     timeout     processing      500ms
>     use-backend coraza-waf-spoa
>     log         global
> 
> spoe-message coraza-req
>     args app=var(txn.waf_app) src-ip=src src-port=src_port dst-ip=dst dst-port=dst_port method=method path=path query=query version=req.ver headers=req.hdrs body=req.body
>     event on-backend-http-request

cat /etc/coraza-spoa/spoa.yml 
> ---
> bind: '127.0.0.1:9000'
> 
> log_file: '/dev/stdout'
> log_level: 'info'
> log_format: 'json'
> 
> applications:
>   - name: 'default'
>     directives: |
>       Include /etc/coraza-spoa/apps/default/v4.7.0/main.conf
>       Include /etc/coraza-spoa/apps/default/v4.7.0/@crs-setup.conf
>       Include /etc/coraza-spoa/apps/default/v4.7.0/@owasp_crs/*.conf
> 
>     response_check: false
>     transaction_ttl_ms: 60000
> 
>     log_level: 'info'
>     log_file: '/var/log/coraza-spoa/default.log'
>     log_format: 'json'
>
>   ...
```


----

## Functionality

* **Package installation**
  * Downloading WAF-Binary
  * Rsyslog & Logrotate if `log.syslog` is enabled

* **Configuration**

  * **Default config**:
    * WAF Configuration at: `/etc/coraza-spoa`
      * Application-Specific rulesets: `/etc/coraza-spoa/apps/<app>/<version>/`
      * [Coraza Core-Ruleset](https://github.com/corazawaf/coraza-coreruleset)
      * [Easy-to-manage Config](https://coraza.io/docs/seclang/directives/)
      * App-specific rule-overrides
    * App-Specific Log-File at `/var/log/coraza-spoa`
      * Log-File => Syslog with App-Specific Tags


  * **Default opt-ins**:
    * ...


  * **Default opt-outs**:
    * ...

----

## Info

* **Note:** this role currently only supports debian-based systems


* **Note:** Most of the role's functionality can be opted in or out.

  For all available options - see the default-config located in [the main defaults-file](https://github.com/O-X-L/ansible-role-haproxy-waf-coraza/blob/latest/defaults/main/1_main.yml)!


* **Warning:** Not every setting/variable you provide will be checked for validity. Bad config might break the role!


* **Info:** You need to configure the WAF-Applications yourself if HAProxy is not managed by the [O-X-L/ansible-role-haproxy](https://github.com/O-X-L/ansible-role-haproxy) Ansible-role (after setting `haproxy.waf.coraza.enable=true`)!


----

### Execution

Run the playbook:
```bash
ansible-playbook -K -D -i inventory/hosts.yml playbook.yml
```

There are also some useful **tags** available:
* install
* logs
* apps => add or update an app
* config => only update config
* rules => only update rules

You can also use the `only_app` runtime-variable to only provision one WAF-App:

```bash
ansible-playbook ... -e only_app=app1 --tags rules
```

To debug errors - you can set the 'debug' variable at runtime:
```bash
ansible-playbook -K -D -i inventory/hosts.yml playbook.yml -e debug=yes
```
