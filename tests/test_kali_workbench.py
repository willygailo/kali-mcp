#!/usr/bin/env python3
"""
Offline Unit & Smoke Test Suite for Kali MCP AI Workbench
---------------------------------------------------------
100% deterministic, zero live network calls. Covers kali_core, kali_parsers,
kali_store (including non-destructive schema migration & dedup), kali_reports,
kali-agent.py CLI flags, and headless PySide6 Desktop GUI initialization.
"""

import importlib.util
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src_private"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import kali_core as kc  # noqa: E402
import kali_mcp_bridge as kmb  # noqa: E402
import kali_parsers as kp  # noqa: E402
import kali_reports as kr  # noqa: E402
import kali_skills as ksk  # noqa: E402
import kali_store as ks  # noqa: E402

VALID_PARSER_KEYS = {
    "nmap_scan",
    "gobuster_scan",
    "dirb_scan",
    "nikto_scan",
    "sqlmap_scan",
    "wpscan_analyze",
    "tls_dns",
    "tls_http_check",
    "origin_dns_tls",
    "tech_waf_fingerprint",
    "subdomain_enum",
    "vhost_fuzz",
    "endpoint_crawl",
    "param_discover",
    "secret_exposure_scan",
    "enum4linux_scan",
    "enum4linux_ng",
    "searchsploit",
    "execute_command",
}


# ==================== 1. kali_core Tests ====================


@pytest.mark.parametrize(
    "raw,exp_scheme,exp_host,exp_port,exp_is_ip,exp_domain",
    [
        ("http://10.10.10.5:8080/app", "http", "10.10.10.5", 8080, True, ""),
        ("https://sub.example.com:8443/api", "https", "sub.example.com", 8443, False, "sub.example.com"),
        ("example.com", "http", "example.com", None, False, "example.com"),
        ("127.0.0.1", "http", "127.0.0.1", None, True, ""),
        ("192.168.1.1:8443", "https", "192.168.1.1", 8443, True, ""),
    ],
)
def test_parse_target_components(raw, exp_scheme, exp_host, exp_port, exp_is_ip, exp_domain):
    info = kc.parse_target_components(raw)
    assert info["scheme"] == exp_scheme
    assert info["host"] == exp_host
    assert info["port"] == exp_port
    assert info["is_ip"] is exp_is_ip
    assert info["domain"] == exp_domain
    assert info["base_url"].startswith(f"{exp_scheme}://")
    assert info["url"].startswith(info["base_url"])


def test_build_shell_command():
    cmd = kc.build_shell_command("dig +short example.com | head -n 5")
    assert cmd == ["bash", "-c", "dig +short example.com | head -n 5"]


def test_all_six_playbooks_resolve_safely():
    expected_keys = {
        "endpoint_api_hunter",
        "domain_origin_vhost",
        "secret_config_audit",
        "full_htb_ctf_recon",
        "web_recon",
        "network_audit",
    }
    assert expected_keys.issubset(set(kc.PLAYBOOKS.keys()))

    for pb_key, pb in kc.PLAYBOOKS.items():
        assert pb["name"]
        assert pb["description"]
        assert len(pb["steps"]) >= 3
        for target in ("https://sub.example.com:8443/app", "10.10.10.5"):
            for step in pb["steps"]:
                api_tool, payload, parser_key = kc.build_playbook_step_call(
                    step,
                    target,
                    wordlist="/usr/share/wordlists/dirb/common.txt",
                    ports="80,443",
                    extra_args="-v",
                )
                assert api_tool
                assert isinstance(payload, dict)
                assert parser_key in VALID_PARSER_KEYS, f"Unexpected parser_key {parser_key} in {pb_key}"
                if api_tool == "execute_command":
                    cmd = payload["command"]
                    assert isinstance(cmd, list) and cmd[:2] == ["bash", "-c"]
                    script = cmd[2]
                    # Must use httpx-toolkit, never bare /usr/bin/httpx
                    assert " httpx " not in f" {script} "
                    assert "/usr/bin/httpx " not in script
                    syntax = subprocess.run(["bash", "-n", "-c", script], capture_output=True, text=True)
                    assert syntax.returncode == 0, f"Invalid bash syntax in {pb_key}: {syntax.stderr}"


def test_playbook_step_quotes_metacharacters():
    step = kc.PLAYBOOKS["domain_origin_vhost"]["steps"][0]
    api_tool, payload, _ = kc.build_playbook_step_call(step, "example.com;id")
    assert api_tool == "execute_command"
    script = payload["command"][2]
    assert "'example.com;id'" in script


def test_all_eighteen_direct_tools_resolve():
    assert len(kc.DIRECT_TOOLS) == 18
    for _label, tool_key in kc.DIRECT_TOOLS:
        api_tool, payload, parser_key = kc.build_direct_tool_call(
            tool_key,
            "https://lab.example.com:8443/api",
            ports="80,443",
            extra_args="",
        )
        assert api_tool
        assert isinstance(payload, dict)
        assert parser_key in VALID_PARSER_KEYS


def test_trim_tool_output_for_llm():
    small = {"success": True, "stdout": "80/tcp open http", "stderr": ""}
    res_small = kc.trim_tool_output_for_llm(small, max_chars=4000)
    assert res_small["stdout"] == "80/tcp open http"
    assert "truncated_for_llm" not in res_small

    big = {"success": True, "stdout": "X" * 25000, "stderr": "Y" * 2000}
    res_big = kc.trim_tool_output_for_llm(big, max_chars=4000)
    assert len(big["stdout"]) == 25000  # Original dict untouched
    assert res_big["truncated_for_llm"] is True
    assert len(res_big["stdout"]) < 4000
    assert "truncated" in res_big["stdout"]


def test_load_playbook_text_and_build_system_prompt(tmp_path):
    pfile = tmp_path / "prompt.txt"
    pfile.write_text("Follow structured recon checklist.", encoding="utf-8")

    resolved, text = kc.load_playbook_text("prompt.txt", base_dirs=[str(tmp_path)])
    assert resolved == str(pfile.resolve())
    assert "structured recon checklist" in text

    discovered = kc.discover_prompt_files(base_dir=str(tmp_path))
    assert str(pfile.resolve()) in discovered

    prompt = kc.build_system_prompt(
        text,
        context_vars={"Target": "10.10.10.5", "Scope": "HTB Box", "Time budget": "medium"},
    )
    assert "Target: 10.10.10.5" in prompt
    assert "Scope: HTB Box" in prompt
    assert "Time budget: medium" in prompt
    assert "structured recon checklist" in prompt


def test_build_system_prompt_includes_skills_sections():
    prompt = kc.build_system_prompt(
        "Follow checklist.",
        skill_index_text="- ad-kerberos-enum [infrastructure]: AD/SMB triage",
        active_skills_text="### Skill: ad-kerberos-enum [infrastructure] (mode: read_only)\nRun enum4linux-ng.",
    )
    assert "## Available Domain Skills" in prompt
    assert "ad-kerberos-enum [infrastructure]: AD/SMB triage" in prompt
    assert "## Active Domain Skills" in prompt
    assert "Run enum4linux-ng." in prompt


# ==================== 1b. kali_skills & kali_mcp_bridge Tests ====================


def test_kali_skills_discover_parse_index_match_and_budget():
    expected_skills = {
        "ad-kerberos-enum",
        "binary-re-pwn-triage",
        "crypto-hash-jwt-triage",
        "forensics-pcap-steg-triage",
        "infra-db-services-enum",
        "privesc-pivoting-transfer",
        "secrets-vcs-config-audit",
        "web-api-vhost-recon",
    }
    skills = ksk.discover_skills([str(REPO_ROOT / "skills")])
    assert set(skills.keys()) == expected_skills

    for name, sk in skills.items():
        assert sk.name == name
        assert sk.category
        assert sk.description
        assert isinstance(sk.ports, list)
        assert isinstance(sk.services, list)
        assert isinstance(sk.keywords, list)
        assert isinstance(sk.recommended_tools, list)
        assert sk.allowed_mode == "read_only"
        assert sk.body

    idx = ksk.render_skill_index(skills)
    for name in expected_skills:
        assert name in idx
    assert len(idx) < 2800

    smb_matches = ksk.match_skills_from_findings(
        [{"port": "445/tcp", "service": "microsoft-ds", "title": "SMB open", "category": "service"}],
        skills=skills,
    )
    assert smb_matches and smb_matches[0].skill.name == "ad-kerberos-enum"

    web_jwt_matches = ksk.match_skills_from_findings(
        [
            {"port": "80/tcp", "service": "http", "title": "HTTP endpoint /api/login", "category": "endpoint"},
            {"port": "-", "service": "secret-scan", "title": "JWT eyJ token in header", "category": "secret"},
        ],
        prompt_text="Inspect API vhost and JWT token",
        skills=skills,
    )
    matched_names = {m.skill.name for m in web_jwt_matches}
    assert {"web-api-vhost-recon", "crypto-hash-jwt-triage"}.issubset(matched_names)

    four_names = [
        "ad-kerberos-enum",
        "web-api-vhost-recon",
        "crypto-hash-jwt-triage",
        "binary-re-pwn-triage",
    ]
    rendered_capped = ksk.render_active_skills_block(four_names, skills)
    assert rendered_capped.count("### Skill:") <= ksk.MAX_ACTIVE_SKILLS
    assert "binary-re-pwn-triage" not in rendered_capped

    tight = ksk.render_active_skills_block(["ad-kerberos-enum", "web-api-vhost-recon"], skills, max_chars=700)
    assert len(tight) <= 700
    assert "[truncated;" in tight


def test_kali_mcp_bridge_capabilities_and_missing_binary():
    caps = kmb.get_available_local_mcps()
    assert isinstance(caps, dict)
    assert set(caps.keys()) == {"cve_mcp", "ghidra_mcp"}
    assert all(isinstance(v, bool) for v in caps.values())

    empty_res = kmb.run_ghidra_triage("")
    assert empty_res["success"] is False
    assert empty_res["return_code"] != 0
    assert empty_res["stderr"]

    missing_res = kmb.run_ghidra_triage("/nonexistent/path/to/missing_sample_bin")
    assert missing_res["success"] is False
    assert missing_res["return_code"] != 0
    assert "not found" in missing_res["stderr"].lower()


# ==================== 2. kali_parsers Tests ====================


def test_redact_secret_and_false_positive_filters():
    assert kp.redact_secret("tiny") == "****"
    assert kp.redact_secret("123456789012") == "****"

    raw_aws = "AKIA9876543210ZYXWVU"
    masked_aws = kp.redact_secret(raw_aws)
    assert masked_aws != raw_aws and raw_aws not in masked_aws and "****" in masked_aws

    raw_uri = "postgres://admin:S3cr3tP4ss!@10.10.10.5:5432/prod"
    masked_uri = kp.redact_secret(raw_uri)
    assert "S3cr3tP4ss!" not in masked_uri and "****" in masked_uri

    assert kp.shannon_entropy("") == 0.0
    assert kp.shannon_entropy("aB3$kL9!xZ2@qW7&") > 3.5

    # False positives rejected
    assert kp.is_false_positive_secret("sha384-oqVuAfXRKap7fdgcCY5uykM6+R9GqQ8K/uxy9rx7HNQlGYl1kPzQho1wx4JwY8wC")
    assert kp.is_false_positive_secret("data:image/png;base64,iVBORw0KGgoAAAANSUhEUg==")
    assert kp.is_false_positive_secret("AKIAIOSFODNN7EXAMPLE")
    assert kp.is_false_positive_secret("YOUR_API_KEY")
    assert kp.is_false_positive_secret("pk_live_51AbCdEfGhIjKlMnOpQrStUvWxYz")
    assert kp.is_false_positive_secret("550e8400-e29b-41d4-a716-446655440000")
    assert kp.is_false_positive_secret("a1b2c3d4e5f60718293a4b5c", "webpack chunk-a1b2c3d4e5f60718293a4b5c.js")

    # Genuine-format tokens accepted (constructed dynamically so static secret scanners don't flag test fixtures)
    sample_aws = "AKIA" + "9876543210ZYXWVU"
    sample_ghp = "ghp_" + "1a2B3c4D5e6F7g8H9i0J1k2L3m4N5o6P7q8R"
    sample_stripe = "sk_" + "live_" + "98AbCdEfGhIjKlMnOpQrStUvWx"
    assert not kp.is_false_positive_secret(sample_aws)
    assert not kp.is_false_positive_secret(sample_ghp)
    assert not kp.is_false_positive_secret(sample_stripe)


def test_parse_secrets_output_always_redacts():
    raw_tokens = [
        "AKIA" + "9876543210ZYXWVU",
        "ghp_" + "1a2B3c4D5e6F7g8H9i0J1k2L3m4N5o6P7q8R",
        "sk_" + "live_" + "98AbCdEfGhIjKlMnOpQrStUvWx",
        "nvapi-" + "AbCdEfGhIjKlMnOpQrStUvWxYz123456",
        "sk-" + "proj-" + "AbCdEfGhIjKlMnOpQrStUvWxYz123456",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwicm9sZSI6ImFkbWluIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
        "postgres://dbadmin:Sup3rS3cr3tP4ss!@10.10.10.2:5432/prod",
    ]
    pem_hdr = "-----BEGIN RSA " + "PRIVATE KEY-----"
    pem_ftr = "-----END RSA " + "PRIVATE KEY-----"
    sample = "\n".join(f"VAR_{i}={tok}" for i, tok in enumerate(raw_tokens)) + (
        f"\n{pem_hdr}\n"
        "MIIEpAIBAAKCAQEAv3ryS3cr3tK3yBodyValue1234567890\n"
        f"{pem_ftr}\n"
        "AKIAIOSFODNN7EXAMPLE\n"
        "pk_" + "live_" + "51AbCdEfGhIjKlMnOpQrStUvWxYz\n"
    )
    findings = kp.parse_secrets_output(sample, "https://lab.example.com")
    assert len(findings) == 8
    for f in findings:
        assert f.category == "secret"
        assert f.severity in ("Critical", "High")
        combined = f"{f.title}\n{f.details}\n{f.evidence}"
        for tok in raw_tokens:
            assert tok not in combined
        assert "MIIEpAIBAAKCAQEAv3ryS3cr3tK3yBodyValue1234567890" not in combined
        assert "Sup3rS3cr3tP4ss!" not in combined


def test_parse_dns_origin_output():
    sample = """
example.com. 300 IN A 93.184.216.34
www.example.com. 300 IN CNAME example.com.
example.com. 300 IN MX 10 mail.example.com.
example.com. 300 IN TXT "v=spf1 include:_spf.google.com +all"
OriginAS: AS15133
CIDR: 93.184.216.0/24
Protocol  : TLSv1.3
Verify return code: 0 (ok)
subject=CN = *.example.com
DNS:example.com, DNS:api.example.com
The site https://example.com is behind Cloudflare WAF.
https://example.com [200 OK] Apache[2.4.49], PHP[7.4]
https://example.com [200] [Example Portal] [Cloudflare]
"""
    findings = kp.parse_dns_origin_output(sample, "https://example.com")
    titles = [f.title for f in findings]
    assert any("93.184.216.34" in t for t in titles)
    assert any("CNAME" in t for t in titles)
    assert any("MX" in t for t in titles)
    assert any("SPF" in t for t in titles)
    assert any("WHOIS" in t for t in titles)
    assert any("SAN" in t for t in titles)
    assert any("Cloudflare" in t for t in titles)
    assert any("Tech fingerprint" in t for t in titles)
    assert any("HTTP probe" in t for t in titles)


def test_parse_subdomains_vhosts_output():
    sample = """
api.example.com
staging.example.com
admin                   [Status: 200, Size: 2048, Words: 120, Lines: 18]
"""
    findings = kp.parse_subdomains_vhosts_output(sample, "https://example.com")
    hosts = {f.host for f in findings}
    assert {"api.example.com", "staging.example.com", "admin.example.com"}.issubset(hosts)
    assert all(f.category == "asset" for f in findings)


def test_parse_endpoints_output_and_misconfig_elevation():
    sample = """
https://example.com/static/bundle.js
https://example.com/.env
/.git/config (Status: 200) [Size: 312]
+ https://example.com/swagger.json (CODE:200|SIZE:5410)
api/v1/health           [Status: 200, Size: 42, Words: 3, Lines: 1]
[+] Valid parameter found: debug
"""
    findings = kp.parse_endpoints_output(sample, "https://example.com")
    assert any(f.category == "endpoint" and "bundle.js" in f.title for f in findings)
    assert any(f.category == "misconfig" and f.severity == "High" and ".env" in f.title for f in findings)
    assert any(f.category == "misconfig" and f.severity == "High" and ".git/config" in f.title for f in findings)
    assert any(f.category == "misconfig" and f.severity == "Medium" and "swagger.json" in f.title for f in findings)
    assert any(f.category == "endpoint" and "debug" in f.title for f in findings)


def test_other_parsers_and_dispatch_dedup():
    e4l = kp.parse_enum4linux_output(
        "Domain Name: LABCORP\n//10.10.10.5/backups Mapping: OK, Listing: OK\nuser:[alice] rid:[0x3e8]\n",
        "10.10.10.5",
    )
    assert any("LABCORP" in f.title for f in e4l)
    assert any("backups" in f.title and f.category == "misconfig" for f in e4l)
    assert any("alice" in f.title for f in e4l)

    nmap_res = kp.parse_nmap_output("80/tcp open http nginx 1.18.0\n80/tcp open http nginx 1.18.0\n", "10.10.10.5")
    assert len(nmap_res) == 1 and nmap_res[0].category == "service"

    nikto_res = kp.parse_nikto_output("+ /phpinfo.php: PHP info file disclosed.", "http://10.10.10.5")
    assert len(nikto_res) == 1 and nikto_res[0].category == "misconfig"

    sqli_res = kp.parse_sqlmap_output("Parameter: id is vulnerable", "http://10.10.10.5/item?id=1")
    assert len(sqli_res) == 1 and sqli_res[0].category == "vulnerability"

    ss_res = kp.parse_searchsploit_json(
        '{"RESULTS_EXPLOIT":[{"Title":"Sample RCE","EDB-ID":"99999","Path":"linux/remote/99999.py"}]}',
        "Sample 1.0",
    )
    assert len(ss_res) == 1 and ss_res[0].category == "exploit"

    # Passive secret scan & dedup via dispatcher
    dispatched = kp.parse_tool_output(
        "endpoint_crawl",
        "https://example.com/app.js\nhttps://example.com/app.js\nkey=AKIA9876543210ZYXWVU\n",
        "https://example.com",
    )
    assert sum(1 for f in dispatched if "app.js" in f.title) == 1
    assert any(f.category == "secret" for f in dispatched)
    for f in dispatched:
        assert "AKIA9876543210ZYXWVU" not in f"{f.title}{f.details}{f.evidence}"


# ==================== 3. kali_store Tests ====================


def test_store_legacy_migration_and_deduplication(tmp_path):
    db_path = tmp_path / "legacy_projects.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(
        """
        CREATE TABLE engagements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            target TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            engagement_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            tool_name TEXT NOT NULL,
            target TEXT NOT NULL,
            raw_output TEXT NOT NULL DEFAULT '',
            ai_analysis TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );
        CREATE TABLE findings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            engagement_id INTEGER NOT NULL,
            scan_id INTEGER,
            severity TEXT NOT NULL,
            host TEXT NOT NULL,
            port TEXT NOT NULL,
            service TEXT NOT NULL,
            title TEXT NOT NULL,
            details TEXT NOT NULL DEFAULT '',
            source_tool TEXT NOT NULL,
            follow_up_tool TEXT NOT NULL DEFAULT '',
            follow_up_target TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );
        CREATE TABLE chat_contexts (
            engagement_id INTEGER PRIMARY KEY,
            messages_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        INSERT INTO engagements (name, target, notes, created_at, updated_at)
        VALUES ('HTB Legacy', '10.10.10.5', 'legacy note', '2026-01-01', '2026-01-01');
        INSERT INTO findings (engagement_id, severity, host, port, service, title, details, source_tool, created_at)
        VALUES (1, 'Info', '10.10.10.5', '22/tcp', 'ssh', 'SSH service exposed', 'OpenSSH', 'nmap_scan', '2026-01-01');
        """
    )
    conn.commit()
    conn.close()

    store = ks.ProjectStore(db_path=str(db_path))
    migrated = store.list_findings(1)
    assert len(migrated) == 1
    assert migrated[0]["category"] == "service"
    assert migrated[0]["evidence"] == ""

    finding_payload = [
        {
            "severity": "Critical",
            "category": "secret",
            "host": "10.10.10.5",
            "port": "-",
            "service": "secret-scan",
            "title": "Exposed AWS Access Key ID (AKIA98****XWVU)",
            "details": "Initial detail",
            "evidence": "KEY=AKIA98****XWVU",
            "source_tool": "secret_exposure_scan",
        }
    ]
    store.save_scan_and_findings(1, "Run 1", "secret_exposure_scan", "10.10.10.5", "raw1", "AI summary 1", finding_payload)
    # Save identical finding a second time with updated details
    finding_payload[0]["details"] = "Updated detail"
    store.save_scan_and_findings(1, "Run 2", "secret_exposure_scan", "10.10.10.5", "raw2", "", finding_payload)

    rows = store.list_findings(1)
    secret_rows = [r for r in rows if r["category"] == "secret"]
    assert len(secret_rows) == 1
    assert secret_rows[0]["details"] == "Updated detail"

    counts = store.get_category_counts(1)
    assert counts["secret"] == 1
    assert counts["service"] == 1

    # Engagement skills non-destructive migration & round-trip
    assert store.get_engagement_skills(1) == []
    store.set_engagement_skills(1, ["ad-kerberos-enum", "web-api-vhost-recon", "AD-KERBEROS-ENUM"])
    assert store.get_engagement_skills(1) == ["ad-kerberos-enum", "web-api-vhost-recon"]
    reopened = ks.ProjectStore(db_path=str(db_path))
    assert reopened.get_engagement_skills(1) == ["ad-kerberos-enum", "web-api-vhost-recon"]


# ==================== 4. kali_reports Tests ====================


def test_markdown_and_html_reports_categorized_escaped_and_ai_fallback():
    engagement = {"name": "HTB Lab", "target": "10.10.10.5", "notes": "user.txt captured"}
    findings = [
        {
            "severity": "Critical",
            "category": "secret",
            "host": "10.10.10.5",
            "port": "-",
            "service": "secret-scan",
            "title": "Exposed GitHub Token (ghp_1a****7q8R)",
            "details": "Redacted token",
            "evidence": "token=ghp_1a****7q8R",
            "source_tool": "secret_exposure_scan",
        },
        {
            "severity": "High",
            "category": "vulnerability",
            "host": "10.10.10.5",
            "port": "web",
            "service": "http",
            "title": "XSS <script>alert(1)</script> | reflected",
            "details": "Line 1\nLine 2 | pipe",
            "evidence": "<script>alert(1)</script>",
            "source_tool": "nikto_scan",
        },
        {
            "severity": "Info",
            "category": "asset",
            "host": "api.example.com",
            "port": "-",
            "service": "dns",
            "title": "Discovered subdomain: api.example.com",
            "details": "Subfinder match",
            "evidence": "api.example.com",
            "source_tool": "subdomain_enum",
        },
        {
            "severity": "Low",
            "category": "endpoint",
            "host": "10.10.10.5",
            "port": "web",
            "service": "http",
            "title": "Discovered hidden parameter 'debug'",
            "details": "Arjun match",
            "evidence": "debug",
            "source_tool": "param_discover",
        },
        {
            "severity": "Info",
            "category": "service",
            "host": "10.10.10.5",
            "port": "80/tcp",
            "service": "http",
            "title": "HTTP web service exposed",
            "details": "nginx 1.18",
            "evidence": "80/tcp open http",
            "source_tool": "nmap_scan",
        },
    ]
    scans = [
        {
            "title": "Recon Run",
            "created_at": "2026-11-25 10:00:00",
            "raw_output": "80/tcp open http",
            "ai_analysis": "Persisted fallback AI triage summary.",
        }
    ]

    md = kr.generate_markdown_report(engagement, findings, scans, ai_summary="")
    assert "## Executive Summary" in md
    assert "### Category Breakdown" in md
    assert "### Exposed Secrets & Credentials (Redacted)" in md
    assert "### Domains, Subdomains, Virtual Hosts & Origin/Real IPs" in md
    assert "### Discovered Endpoints, APIs & Hidden Parameters" in md
    assert "### Vulnerabilities & Misconfigurations" in md
    assert "### Open Ports, Services & Exploit References" in md
    assert "Line 1<br>Line 2 \\| pipe" in md
    assert "Persisted fallback AI triage summary." in md

    html_doc = kr.generate_html_report(engagement, findings, scans, ai_summary="")
    assert "Executive Summary" in html_doc
    assert "Category Breakdown" in html_doc
    assert "Exposed Secrets &amp; Credentials (Redacted)" in html_doc
    assert "Persisted fallback AI triage summary." in html_doc
    assert "<script>alert(1)</script>" not in html_doc
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html_doc


# ==================== 5. kali-agent.py CLI Tests ====================


def test_cli_list_playbooks_and_help_offline():
    env = dict(os.environ, PYTHONPATH=str(SRC_DIR))
    help_proc = subprocess.run(
        [sys.executable, str(SRC_DIR / "kali-agent.py"), "--help"],
        capture_output=True,
        text=True,
        env=env,
        timeout=15,
    )
    assert help_proc.returncode == 0
    assert "--list-playbooks" in help_proc.stdout
    assert "--list-skills" in help_proc.stdout
    assert "--skill" in help_proc.stdout
    assert "--auto-skills" in help_proc.stdout
    assert "--run-playbook" in help_proc.stdout
    assert "--ai-triage" in help_proc.stdout

    list_proc = subprocess.run(
        [sys.executable, str(SRC_DIR / "kali-agent.py"), "--list-playbooks"],
        capture_output=True,
        text=True,
        env=env,
        timeout=15,
    )
    assert list_proc.returncode == 0
    for pb_key in (
        "endpoint_api_hunter",
        "domain_origin_vhost",
        "secret_config_audit",
        "full_htb_ctf_recon",
        "web_recon",
        "network_audit",
    ):
        assert pb_key in list_proc.stdout

    skills_proc = subprocess.run(
        [sys.executable, str(SRC_DIR / "kali-agent.py"), "--list-skills"],
        capture_output=True,
        text=True,
        env=env,
        timeout=15,
    )
    assert skills_proc.returncode == 0
    for sk_name in (
        "ad-kerberos-enum",
        "binary-re-pwn-triage",
        "crypto-hash-jwt-triage",
        "forensics-pcap-steg-triage",
        "infra-db-services-enum",
        "privesc-pivoting-transfer",
        "secrets-vcs-config-audit",
        "web-api-vhost-recon",
    ):
        assert sk_name in skills_proc.stdout

    bad_skill = subprocess.run(
        [sys.executable, str(SRC_DIR / "kali-agent.py"), "--skill", "nonexistent-skill-xyz"],
        capture_output=True,
        text=True,
        env=env,
        timeout=15,
    )
    assert bad_skill.returncode != 0
    assert "Unknown skill" in bad_skill.stdout

    agent_spec = importlib.util.spec_from_file_location("kali_agent_mod", str(SRC_DIR / "kali-agent.py"))
    assert agent_spec is not None and agent_spec.loader is not None
    agent_mod = importlib.util.module_from_spec(agent_spec)
    agent_spec.loader.exec_module(agent_mod)

    catalog = ksk.discover_skills([str(REPO_ROOT / "skills")])
    msgs = [{"role": "system", "content": ""}]
    active, changed = agent_mod._handle_skill_cmd("ad-kerberos-enum", [], catalog, msgs, [], "", None)
    assert changed is True and active == ["ad-kerberos-enum"]
    active, changed = agent_mod._handle_skill_cmd("ad-kerberos-enum", active, catalog, msgs, [], "", None)
    assert changed is True and active == []
    active, changed = agent_mod._handle_skill_cmd(
        "auto",
        [],
        catalog,
        msgs,
        [{"port": "445/tcp", "service": "smb", "title": "SMB open"}],
        "10.10.10.5",
        None,
    )
    assert changed is True and "ad-kerberos-enum" in active
    prompt_txt = agent_mod._compose_prompt(None, catalog, active)
    assert "## Available Domain Skills" in prompt_txt
    assert "## Active Domain Skills" in prompt_txt
    active, changed = agent_mod._handle_skill_cmd("off", active, catalog, msgs, [], "", None)
    assert changed is True and active == []


# ==================== 6. Headless PySide6 GUI Smoke Test ====================


def test_headless_gui_smoke(tmp_path, monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    assert app is not None

    spec = importlib.util.spec_from_file_location("kali_gui_mod", str(SRC_DIR / "kali-gui.py"))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    store = ks.ProjectStore(db_path=str(tmp_path / "gui_smoke.db"))
    win = mod.KaliGuiWindow(store=store)
    try:
        expected_direct_tools = 18 + int(kc.has_cve_mcp()) + int(kc.has_ghidra_mcp())
        assert win.playbook_combo.count() == 6
        assert win.direct_tool_combo.count() == expected_direct_tools
        assert win.findings_table.columnCount() == 7
        assert win.category_filter_combo.count() == 8
        assert len(win.available_skills) == 8

        win.toggle_skill("ad-kerberos-enum")
        assert "ad-kerberos-enum" in win.active_skills
        assert "ad-kerberos-enum" in win._effective_system_prompt()

        from kali_gui_dialogs import SkillSelectorDialog

        dlg = SkillSelectorDialog(parent=win, skills=win.available_skills, active_skills=win.active_skills)
        try:
            assert dlg.skill_list.count() == 8
            dlg.search_input.setText("ad-kerberos-enum")
            assert dlg.skill_list.count() == 1
            assert dlg.selected_skills == ["ad-kerberos-enum"]
        finally:
            dlg.close()
    finally:
        win.close()
