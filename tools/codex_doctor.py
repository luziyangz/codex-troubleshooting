#!/usr/bin/env python3
"""Read-only, aggregate-only Codex state diagnostics. No network or state writes."""
import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

VERSION = '0.1.0'
MAX_STATE_BYTES = 32 * 1024 * 1024


def choose_home(explicit=None):
    value = explicit or os.environ.get('CODEX_HOME')
    return Path(value).expanduser().resolve() if value else (Path.home() / '.codex').resolve()


def inspect_state(path):
    result = {'exists': path.is_file()}
    if not result['exists']:
        result['status'] = 'missing'
        return result
    try:
        if path.stat().st_size > MAX_STATE_BYTES:
            result['status'] = 'size_limit'
            return result
        raw = path.read_bytes()
        result['size_bytes'] = len(raw)
        text = raw.decode('utf-8-sig')
        result['nul_characters'] = text.count('\0')
        data = json.loads(text)
    except UnicodeDecodeError:
        result['status'] = 'invalid_utf8'
        return result
    except json.JSONDecodeError:
        result['status'] = 'invalid_json'
        return result
    except OSError:
        result['status'] = 'unreadable'
        return result
    if not isinstance(data, dict):
        result['status'] = 'invalid_root_type'
        return result
    result['status'] = 'valid'
    projects = data.get('local-projects', {})
    assignments = data.get('thread-project-assignments', {})
    result['projects_key_present'] = 'local-projects' in data
    result['assignments_key_present'] = 'thread-project-assignments' in data
    if not isinstance(projects, dict) or not isinstance(assignments, dict):
        result['status'] = 'schema_not_supported'
        return result
    result['local_project_records'] = len(projects)
    result['assignment_records'] = len(assignments)
    local = [item for item in assignments.values() if isinstance(item, dict) and item.get('projectKind') == 'local']
    result['local_assignment_records'] = len(local)
    result['local_assignments_without_cached_project'] = sum(not isinstance(item.get('projectId'), str) or item['projectId'] not in projects for item in local)
    return result


def inspect_database(path, location):
    result = {'file': path.name, 'location': location}
    database = None
    try:
        database = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True, timeout=2)
        database.execute('PRAGMA query_only = ON')
        tables = {row[0] for row in database.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        result['status'] = 'readable'
        for table in ('projects', 'project_roots', 'threads'):
            if table in tables:
                result[table + '_records'] = database.execute('SELECT count(*) FROM ' + table).fetchone()[0]
        if 'threads' in tables:
            columns = {row[1] for row in database.execute('PRAGMA table_info(threads)')}
            if 'project_id' in columns:
                result['threads_with_project_id'] = database.execute("SELECT count(*) FROM threads WHERE project_id IS NOT NULL AND project_id <> ''").fetchone()[0]
        if not {'projects', 'threads'} & tables:
            result['status'] = 'schema_not_supported'
    except (sqlite3.Error, OSError, ValueError):
        result['status'] = 'unavailable'
    finally:
        if database is not None:
            database.close()
    return result


def diagnose(home):
    report = {'schema_version': 1, 'tool_version': VERSION,
              'checked_at': datetime.now(timezone.utc).isoformat(), 'platform': sys.platform,
              'codex_home_exists': home.is_dir(), 'read_only': True}
    report['state'] = inspect_state(home / '.codex-global-state.json')
    report['backup_state'] = inspect_state(home / '.codex-global-state.json.bak')
    databases = []
    discovery_errors = []
    for folder, location in ((home, 'root'), (home / 'sqlite', 'nested_sqlite')):
        if not folder.is_dir():
            continue
        try:
            candidates = [path for path in folder.iterdir() if path.is_file() and re.fullmatch(r'state_\d+\.sqlite', path.name)]
            for path in sorted(candidates, key=lambda item: item.name):
                databases.append(inspect_database(path, location))
        except OSError:
            discovery_errors.append(location)
    report['databases'] = databases
    if discovery_errors:
        report['database_discovery_errors'] = discovery_errors
    findings = []
    state = report['state']
    if state['status'] in ('invalid_json', 'invalid_utf8', 'invalid_root_type'):
        findings.append({'code':'STATE_PARSE_FAILED', 'meaning':'当前状态文件无法按预期解析；先备份并检查启动日志，损坏原因尚不能确定。'})
    elif state['status'] == 'missing':
        findings.append({'code':'STATE_MISSING', 'meaning':'该目录没有主状态文件；先确认实际 CODEX_HOME，不据此判断聊天丢失。'})
    elif state['status'] not in ('valid',):
        findings.append({'code':'STATE_CHECK_INCOMPLETE', 'meaning':'状态结构、大小或读取权限不在本工具可检查范围内。'})
    readable = [item for item in databases if item['status'] == 'readable']
    if any(item.get('projects_records', 0) > 0 for item in readable) and state.get('local_project_records', 0) == 0:
        findings.append({'code':'PROJECT_DEFINITIONS_WITHOUT_CACHE', 'meaning':'某份数据库仍有项目定义，而主配置没有可识别的项目缓存；这是恢复线索，不代表该数据库一定是当前活动库。'})
    if state.get('local_assignments_without_cached_project', 0):
        findings.append({'code':'LOCAL_ASSIGNMENT_CACHE_MISMATCH', 'meaning':'部分本地关联没有对应缓存项目，需结合版本与应用接口核对。'})
    if len(databases) > 1:
        findings.append({'code':'MULTIPLE_DATABASE_CANDIDATES', 'meaning':'存在多份状态数据库；本工具不会自动选择、合并或恢复其中一份。'})
    if not findings:
        findings.append({'code':'NO_STRUCTURAL_FAILURE_FOUND', 'meaning':'未发现本工具能识别的结构异常；不等于项目已恢复，请继续核对账号、主机、分组、过滤和归档。'})
    report['findings'] = findings
    report['limits'] = ['不读取登录凭据、聊天正文、项目名称或工作目录；不自动扫描日志。',
                        '数据库计数可能包含内部会话，不等于侧栏用户聊天数。',
                        '报告不确认活动数据库，不推断文件损坏的底层原因，不执行修复。']
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codex-home', help='Explicit Codex state directory')
    parser.add_argument('--output', type=Path, help='Write aggregate JSON to a NEW file; existing files are not replaced')
    args = parser.parse_args(argv)
    report = diagnose(choose_home(args.codex_home))
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        try:
            with args.output.open('x', encoding='utf-8') as file:
                file.write(rendered)
        except OSError:
            parser.exit(2, 'Cannot create report file. Use a new path in an existing writable directory.\n')
        print('Aggregate report saved. Review it before sharing.')
    else:
        print(rendered)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
