"""Native productivity cockpit bridge server (A3 core parity slice)."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import threading
import time
from typing import Any
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

from .productivity_config import (
    ProductivityCockpitConfig,
    ensure_path_within_project_root,
    load_cockpit_config,
    resolve_optional_project_relative_path,
    resolve_project_relative_path,
)


SERVICE_NAME = "specify-productivity-cockpit"
LOGGER = logging.getLogger("specify_cli.productivity_bridge")
CANONICAL_FEATURE_BRANCH_RE = re.compile(r"^(?P<prefix>\d{3})-(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)$")
TASK_SECTION_ORDER = ("Active", "Waiting On", "Someday", "Done")
TASK_LINE_RE = re.compile(r"^\s*-\s*\[(?P<checked>[ xX])\]\s*(?P<body>.+?)\s*$")
MAX_REQUEST_BODY_BYTES = 256_000
MAX_PROMPT_CHARS = 8_000
MAX_EXEC_OUTPUT_CHARS = 20_000
MAX_CLI_ARGS = 12
MAX_CLI_ARG_CHARS = 140
MAX_MEMORY_FILES = 300
MAX_MEMORY_FILE_BYTES = 350_000
MAX_MEMORY_CONTENT_BYTES = 350_000
ALLOWED_CLI_ARG_RE = re.compile(r"^--[a-zA-Z0-9][a-zA-Z0-9-]*(=[a-zA-Z0-9._:/+\-]{1,120})?$")
ALLOWED_AI_CLIS = frozenset(
    {
        "claude",
        "gemini",
        "copilot",
        "codex",
        "qwen",
        "opencode",
        "codebuddy",
        "qoder",
        "q",
        "amp",
        "shai",
        "cursor-agent",
        "ollama",
    }
)

HTML_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Spec Kit Productivity Cockpit</title>
  <style>
    :root {
      --bg: #f6f4ef;
      --panel: #ffffff;
      --panel-soft: #fbfaf6;
      --border: #e5e1d8;
      --text: #1f2329;
      --muted: #59636e;
      --accent: #d06f4d;
      --accent-2: #a84c2f;
      --ok: #2f7d45;
      --warn: #9a6a11;
      --error: #a12f2f;
      --shadow: 0 10px 30px rgba(20, 30, 40, 0.08);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", "Inter", ui-sans-serif, system-ui, sans-serif;
      background: radial-gradient(circle at 10% 10%, #fffdf7, var(--bg));
      color: var(--text);
    }
    .layout {
      display: grid;
      grid-template-columns: 260px 1fr;
      min-height: 100vh;
    }
    .sidebar {
      border-right: 1px solid var(--border);
      background: linear-gradient(180deg, #fffefb, #f5f3ee);
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 18px;
    }
    .brand h1 {
      margin: 0;
      font-size: 1.15rem;
      letter-spacing: 0.01em;
    }
    .brand p {
      margin: 4px 0 0;
      color: var(--muted);
      font-size: 0.84rem;
    }
    .nav {
      display: grid;
      gap: 8px;
    }
    .nav button {
      border: 1px solid var(--border);
      background: var(--panel-soft);
      color: var(--text);
      text-align: left;
      border-radius: 10px;
      padding: 10px 12px;
      font-size: 0.9rem;
      cursor: pointer;
    }
    .nav button.active {
      border-color: var(--accent);
      background: #fff2ec;
      color: var(--accent-2);
      font-weight: 600;
    }
    .timer {
      margin-top: auto;
      border: 1px solid var(--border);
      border-radius: 12px;
      background: var(--panel);
      padding: 12px;
      box-shadow: var(--shadow);
    }
    .timer .value {
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 1.15rem;
      font-weight: 700;
      margin: 6px 0 10px;
    }
    .timer button {
      width: 100%;
      border: 1px solid var(--border);
      background: #fff8f2;
      color: var(--accent-2);
      border-radius: 8px;
      padding: 8px;
      cursor: pointer;
      font-weight: 600;
    }
    .main {
      padding: 20px 22px 30px;
    }
    .header {
      display: flex;
      align-items: center;
      gap: 12px;
      justify-content: space-between;
      margin-bottom: 16px;
    }
    .header h2 {
      margin: 0;
      font-size: 1.2rem;
    }
    .meta {
      color: var(--muted);
      font-size: 0.85rem;
      margin-top: 2px;
    }
    .header .actions {
      display: flex;
      gap: 8px;
    }
    button.primary, button.secondary {
      border-radius: 9px;
      border: 1px solid var(--border);
      padding: 8px 11px;
      cursor: pointer;
      font-size: 0.85rem;
      font-weight: 600;
    }
    button.primary {
      background: linear-gradient(180deg, #ef8d67, var(--accent));
      color: #fff;
      border-color: #b45434;
    }
    button.secondary {
      background: var(--panel-soft);
      color: var(--text);
    }
    .status-banner {
      margin-bottom: 14px;
      border: 1px solid var(--border);
      background: var(--panel);
      padding: 10px 12px;
      border-radius: 10px;
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      font-size: 0.85rem;
    }
    .status-banner strong { color: var(--accent-2); }
    .views > section { display: none; }
    .views > section.active { display: block; }
    .board {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(4, minmax(200px, 1fr));
    }
    .col {
      border: 1px solid var(--border);
      background: var(--panel);
      border-radius: 12px;
      padding: 10px;
      box-shadow: var(--shadow);
    }
    .col h3 {
      margin: 0 0 8px;
      font-size: 0.9rem;
    }
    .col ul {
      list-style: none;
      margin: 0;
      padding: 0;
      display: grid;
      gap: 8px;
      min-height: 90px;
    }
    .task {
      border: 1px solid var(--border);
      background: var(--panel-soft);
      border-radius: 8px;
      padding: 8px;
      display: grid;
      grid-template-columns: auto 1fr auto;
      gap: 6px;
      align-items: start;
    }
    .task input[type="text"] {
      border: 0;
      background: transparent;
      width: 100%;
      color: var(--text);
      font-size: 0.85rem;
      outline: none;
    }
    .task.done input[type="text"] {
      text-decoration: line-through;
      color: var(--muted);
    }
    .task button {
      border: 0;
      background: transparent;
      color: var(--muted);
      cursor: pointer;
      padding: 0 4px;
      font-size: 0.9rem;
    }
    .col .add {
      margin-top: 8px;
      width: 100%;
      border: 1px dashed var(--border);
      background: #fff;
      border-radius: 7px;
      cursor: pointer;
      font-size: 0.82rem;
      padding: 7px;
      color: var(--muted);
    }
    .memory-grid {
      display: grid;
      grid-template-columns: 240px 1fr;
      gap: 12px;
    }
    .memory-files, .memory-editor {
      border: 1px solid var(--border);
      background: var(--panel);
      border-radius: 12px;
      box-shadow: var(--shadow);
    }
    .memory-files {
      overflow: auto;
      max-height: 70vh;
      padding: 8px;
      display: grid;
      gap: 6px;
    }
    .memory-files button {
      border: 1px solid var(--border);
      border-radius: 8px;
      background: #fff;
      text-align: left;
      font-size: 0.82rem;
      padding: 7px 8px;
      cursor: pointer;
      color: var(--text);
      word-break: break-all;
    }
    .memory-files button.active {
      border-color: var(--accent);
      background: #fff2ec;
    }
    .memory-editor {
      padding: 10px;
      display: grid;
      gap: 8px;
    }
    .memory-editor textarea {
      width: 100%;
      min-height: 54vh;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 0.82rem;
      resize: vertical;
      outline: none;
    }
    .pulse-list {
      display: grid;
      gap: 8px;
    }
    .pulse-item {
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 9px 10px;
      background: var(--panel);
      display: flex;
      justify-content: space-between;
      gap: 8px;
      font-size: 0.85rem;
    }
    .pulse-item small { color: var(--muted); display: block; }
    .ok { color: var(--ok); font-weight: 700; }
    .warn { color: var(--warn); font-weight: 700; }
    .error { color: var(--error); font-weight: 700; }
    .chat {
      border: 1px solid var(--border);
      border-radius: 12px;
      background: var(--panel);
      box-shadow: var(--shadow);
      display: grid;
      grid-template-rows: 1fr auto;
      min-height: 62vh;
    }
    .chat-history {
      padding: 12px;
      overflow: auto;
      display: grid;
      gap: 9px;
    }
    .bubble {
      border-radius: 10px;
      padding: 9px 10px;
      max-width: 85%;
      white-space: pre-wrap;
      font-size: 0.84rem;
      line-height: 1.4;
      border: 1px solid var(--border);
    }
    .bubble.user { margin-left: auto; background: #fff2ec; }
    .bubble.bot { background: #ffffff; }
    .chat form {
      border-top: 1px solid var(--border);
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 8px;
      padding: 10px;
    }
    .chat input {
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 9px 10px;
      font-size: 0.85rem;
      outline: none;
    }
    .spotlight {
      position: fixed;
      inset: 0;
      background: rgba(20, 22, 26, 0.45);
      display: none;
      align-items: flex-start;
      justify-content: center;
      padding-top: 11vh;
      z-index: 40;
    }
    .spotlight.active { display: flex; }
    .spotlight .panel {
      width: min(720px, 94vw);
      background: #fff;
      border-radius: 12px;
      border: 1px solid var(--border);
      box-shadow: 0 14px 45px rgba(0, 0, 0, 0.25);
      overflow: hidden;
    }
    .spotlight input {
      width: 100%;
      border: 0;
      border-bottom: 1px solid var(--border);
      padding: 14px;
      outline: none;
      font-size: 1rem;
    }
    .spotlight ul {
      margin: 0;
      padding: 8px;
      list-style: none;
      max-height: 320px;
      overflow: auto;
      display: grid;
      gap: 6px;
    }
    .spotlight li {
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px;
      background: #fff;
      font-size: 0.84rem;
      cursor: pointer;
    }
    .notice {
      margin-top: 10px;
      font-size: 0.82rem;
      color: var(--muted);
    }
    @media (max-width: 980px) {
      .layout { grid-template-columns: 1fr; }
      .sidebar { border-right: 0; border-bottom: 1px solid var(--border); }
      .board { grid-template-columns: 1fr 1fr; }
      .memory-grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">
        <h1>Productivity Cockpit</h1>
        <p>Native A3 core</p>
      </div>
      <div class="nav">
        <button class="active" data-view="tasks">Tasks</button>
        <button data-view="memory">Memory</button>
        <button data-view="pulse">Pulse</button>
        <button data-view="chat">AI Chat</button>
      </div>
      <div class="timer">
        <div style="font-size:0.78rem;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;">Focus Timer</div>
        <div class="value" id="timerValue">25:00</div>
        <button id="timerToggle">Start</button>
      </div>
    </aside>
    <main class="main">
      <div class="header">
        <div>
          <h2 id="viewTitle">Tasks</h2>
          <div class="meta" id="metaLine">Loading...</div>
        </div>
        <div class="actions">
          <button class="secondary" id="openSpotlight">Spotlight (Ctrl+K)</button>
          <button class="secondary" id="refreshBtn">Refresh</button>
          <button class="primary" id="saveTasksBtn">Save Tasks</button>
        </div>
      </div>
      <div class="status-banner" id="statusBanner"></div>
      <div class="views">
        <section id="view-tasks" class="active">
          <div class="board" id="board"></div>
          <div class="notice" id="driftNotice"></div>
        </section>
        <section id="view-memory">
          <div class="memory-grid">
            <div class="memory-files" id="memoryFiles"></div>
            <div class="memory-editor">
              <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;">
                <strong id="memoryPathLabel">Select a memory file</strong>
                <button class="primary" id="saveMemoryBtn">Save Memory</button>
              </div>
              <textarea id="memoryEditor" placeholder="Memory content..."></textarea>
            </div>
          </div>
        </section>
        <section id="view-pulse">
          <div class="pulse-list" id="pulseList"></div>
        </section>
        <section id="view-chat">
          <div class="chat">
            <div class="chat-history" id="chatHistory"></div>
            <form id="chatForm">
              <input id="chatInput" placeholder="Ask from cockpit context..." />
              <button class="primary" type="submit">Send</button>
            </form>
          </div>
        </section>
      </div>
    </main>
  </div>

  <div class="spotlight" id="spotlightOverlay">
    <div class="panel">
      <input id="spotlightInput" placeholder="Search tasks or memory... (Esc to close)" />
      <ul id="spotlightResults"></ul>
    </div>
  </div>

  <script>
    const sections = ['Active', 'Waiting On', 'Someday', 'Done'];
    const state = {
      status: null,
      tasks: { sections: {} },
      memoryFiles: [],
      memoryCurrentPath: '',
      driftCursor: 0,
      spotlightIndex: []
    };

    function safeText(value) {
      return String(value ?? '');
    }

    function renderStatusBanner() {
      const host = state.status?.host || '';
      const port = state.status?.port || '';
      const root = state.status?.project_root || '';
      const tasks = state.status?.paths?.tasks || '';
      const memory = state.status?.paths?.memory || '';
      const banner = document.getElementById('statusBanner');
      banner.replaceChildren();
      const pairs = [
        ['Service', state.status?.service || 'n/a'],
        ['Host', host + ':' + port],
        ['Tasks', tasks || 'n/a'],
        ['Memory', memory || 'n/a'],
        ['Root', root || 'n/a']
      ];
      for (const [label, value] of pairs) {
        const el = document.createElement('div');
        const strong = document.createElement('strong');
        strong.textContent = label + ': ';
        const span = document.createElement('span');
        span.textContent = safeText(value);
        el.append(strong, span);
        banner.appendChild(el);
      }
      document.getElementById('metaLine').textContent = `Uptime ${Math.round(state.status?.uptime_seconds || 0)}s`;
    }

    function createTaskItem(section, item) {
      const li = document.createElement('li');
      li.className = 'task' + (item.checked ? ' done' : '');

      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.checked = !!item.checked;
      checkbox.addEventListener('change', () => {
        li.classList.toggle('done', checkbox.checked);
      });

      const input = document.createElement('input');
      input.type = 'text';
      input.value = safeText(item.body || item.title || '');

      const remove = document.createElement('button');
      remove.type = 'button';
      remove.textContent = '×';
      remove.title = 'Remove task';
      remove.addEventListener('click', () => li.remove());

      li.append(checkbox, input, remove);
      return li;
    }

    function renderBoard() {
      const board = document.getElementById('board');
      board.replaceChildren();
      for (const section of sections) {
        const col = document.createElement('div');
        col.className = 'col';
        const h = document.createElement('h3');
        h.textContent = section;
        const ul = document.createElement('ul');
        ul.dataset.section = section;
        const list = state.tasks.sections?.[section] || [];
        for (const item of list) {
          ul.appendChild(createTaskItem(section, item));
        }
        const add = document.createElement('button');
        add.type = 'button';
        add.className = 'add';
        add.textContent = '+ Add task';
        add.addEventListener('click', () => {
          ul.appendChild(createTaskItem(section, {body: '', checked: false}));
        });
        col.append(h, ul, add);
        board.appendChild(col);
      }
    }

    function collectBoardPayload() {
      const payload = { sections: {} };
      for (const section of sections) {
        const ul = document.querySelector(`ul[data-section="${section}"]`);
        const items = [];
        if (ul) {
          for (const row of ul.children) {
            const checkbox = row.querySelector('input[type="checkbox"]');
            const text = row.querySelector('input[type="text"]');
            const body = safeText(text?.value).trim();
            if (!body) continue;
            items.push({ body, checked: !!checkbox?.checked });
          }
        }
        payload.sections[section] = items;
      }
      return payload;
    }

    function renderMemoryFiles() {
      const wrap = document.getElementById('memoryFiles');
      wrap.replaceChildren();
      for (const item of state.memoryFiles) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.textContent = safeText(item.path);
        btn.classList.toggle('active', item.path === state.memoryCurrentPath);
        btn.addEventListener('click', () => loadMemoryFile(item.path));
        wrap.appendChild(btn);
      }
      if (!state.memoryFiles.length) {
        const p = document.createElement('div');
        p.className = 'notice';
        p.textContent = 'No memory files found.';
        wrap.appendChild(p);
      }
    }

    async function loadMemoryFile(path) {
      const r = await fetch('/api/memory?path=' + encodeURIComponent(path));
      const data = await r.json();
      if (!r.ok) throw new Error(data.error || 'Failed to load memory file');
      state.memoryCurrentPath = data.path;
      document.getElementById('memoryPathLabel').textContent = safeText(data.path);
      document.getElementById('memoryEditor').value = safeText(data.content);
      renderMemoryFiles();
    }

    function renderPulse(pulse) {
      const list = document.getElementById('pulseList');
      list.replaceChildren();
      const items = [
        ...(pulse.essential_files || []),
        ...(pulse.min_folders || []),
        { label: 'tasks.total', exists: true, detail: String(pulse.task_counts?.total || 0) }
      ];
      for (const item of items) {
        const row = document.createElement('div');
        row.className = 'pulse-item';
        const left = document.createElement('div');
        left.textContent = safeText(item.label);
        const right = document.createElement('div');
        right.className = item.exists ? 'ok' : (item.warning ? 'warn' : 'error');
        right.textContent = item.exists ? 'ok' : (item.warning ? 'warn' : 'missing');
        const detail = document.createElement('small');
        detail.textContent = safeText(item.detail || '');
        const rightWrap = document.createElement('div');
        rightWrap.append(right, detail);
        row.append(left, rightWrap);
        list.appendChild(row);
      }
    }

    function addChatBubble(text, cls) {
      const history = document.getElementById('chatHistory');
      const bubble = document.createElement('div');
      bubble.className = 'bubble ' + cls;
      bubble.textContent = safeText(text);
      history.appendChild(bubble);
      history.scrollTop = history.scrollHeight;
    }

    function switchView(view) {
      document.querySelectorAll('.nav button').forEach((btn) => btn.classList.toggle('active', btn.dataset.view === view));
      document.querySelectorAll('.views > section').forEach((section) => {
        section.classList.toggle('active', section.id === `view-${view}`);
      });
      document.getElementById('viewTitle').textContent = {
        tasks: 'Tasks',
        memory: 'Memory',
        pulse: 'Pulse',
        chat: 'AI Chat'
      }[view] || 'Cockpit';
      document.getElementById('saveTasksBtn').style.display = view === 'tasks' ? '' : 'none';
    }

    function buildSpotlightIndex() {
      const rows = [];
      for (const section of sections) {
        for (const item of (state.tasks.sections?.[section] || [])) {
          rows.push({ type: 'task', section, text: item.body || item.title || '' });
        }
      }
      for (const file of state.memoryFiles) {
        rows.push({ type: 'memory', section: file.path, text: file.preview || file.path });
      }
      state.spotlightIndex = rows;
    }

    function renderSpotlightResults(query) {
      const ul = document.getElementById('spotlightResults');
      ul.replaceChildren();
      const normalized = query.trim().toLowerCase();
      const rows = normalized
        ? state.spotlightIndex.filter((row) => row.text.toLowerCase().includes(normalized)).slice(0, 25)
        : state.spotlightIndex.slice(0, 25);
      for (const row of rows) {
        const li = document.createElement('li');
        li.textContent = `${row.type.toUpperCase()} · ${row.section} · ${row.text}`;
        li.addEventListener('click', () => {
          if (row.type === 'memory') {
            switchView('memory');
            loadMemoryFile(row.section).catch(console.error);
          } else {
            switchView('tasks');
          }
          hideSpotlight();
        });
        ul.appendChild(li);
      }
      if (!rows.length) {
        const li = document.createElement('li');
        li.textContent = 'No results';
        ul.appendChild(li);
      }
    }

    function showSpotlight() {
      const overlay = document.getElementById('spotlightOverlay');
      overlay.classList.add('active');
      const input = document.getElementById('spotlightInput');
      input.value = '';
      renderSpotlightResults('');
      input.focus();
    }

    function hideSpotlight() {
      document.getElementById('spotlightOverlay').classList.remove('active');
    }

    async function refreshAll() {
      const [statusRes, tasksRes, memoryRes, pulseRes, driftRes] = await Promise.all([
        fetch('/api/status'),
        fetch('/api/tasks'),
        fetch('/api/memory'),
        fetch('/api/pulse'),
        fetch('/api/drift?cursor=' + encodeURIComponent(String(state.driftCursor || 0)))
      ]);
      const status = await statusRes.json();
      const tasks = await tasksRes.json();
      const memory = await memoryRes.json();
      const pulse = await pulseRes.json();
      const drift = await driftRes.json();
      if (!statusRes.ok) throw new Error(status.error || 'status error');
      if (!tasksRes.ok) throw new Error(tasks.error || 'tasks error');
      if (!memoryRes.ok) throw new Error(memory.error || 'memory error');
      if (!pulseRes.ok) throw new Error(pulse.error || 'pulse error');
      if (!driftRes.ok) throw new Error(drift.error || 'drift error');

      state.status = status;
      state.tasks = tasks;
      state.memoryFiles = memory.files || [];
      state.driftCursor = drift.cursor || state.driftCursor;

      renderStatusBanner();
      renderBoard();
      renderMemoryFiles();
      renderPulse(pulse);
      buildSpotlightIndex();

      const driftNotice = document.getElementById('driftNotice');
      const changed = drift.changed || [];
      driftNotice.textContent = changed.length ? `Drift watcher: ${changed.length} changed file(s) detected.` : 'Drift watcher: no recent changes.';

      if (!state.memoryCurrentPath && state.memoryFiles.length) {
        await loadMemoryFile(state.memoryFiles[0].path);
      }
    }

    async function saveTasks() {
      const payload = collectBoardPayload();
      const r = await fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.error || 'Failed to save tasks');
      await refreshAll();
    }

    async function saveMemory() {
      if (!state.memoryCurrentPath) return;
      const content = document.getElementById('memoryEditor').value;
      const r = await fetch('/api/memory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: state.memoryCurrentPath, content })
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.error || 'Failed to save memory');
      await refreshAll();
    }

    async function sendChat(prompt) {
      addChatBubble(prompt, 'user');
      const r = await fetch('/api/exec', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt })
      });
      const data = await r.json();
      if (!r.ok) {
        addChatBubble('Error: ' + safeText(data.error || 'request failed'), 'bot');
        return;
      }
      const output = [data.stdout || '', data.stderr || ''].filter(Boolean).join('\\n');
      addChatBubble(output || '(no output)', 'bot');
    }

    function setupTimer() {
      let running = false;
      let remaining = 25 * 60;
      let timerRef = null;
      const value = document.getElementById('timerValue');
      const toggle = document.getElementById('timerToggle');

      const render = () => {
        const m = Math.floor(remaining / 60).toString().padStart(2, '0');
        const s = Math.floor(remaining % 60).toString().padStart(2, '0');
        value.textContent = `${m}:${s}`;
      };
      render();

      toggle.addEventListener('click', () => {
        if (running) {
          running = false;
          toggle.textContent = 'Start';
          if (timerRef) clearInterval(timerRef);
          return;
        }
        running = true;
        toggle.textContent = 'Pause';
        timerRef = setInterval(() => {
          if (!running) return;
          remaining -= 1;
          if (remaining < 0) remaining = 25 * 60;
          render();
        }, 1000);
      });
    }

    function setupInteractions() {
      document.querySelectorAll('.nav button').forEach((btn) => {
        btn.addEventListener('click', () => switchView(btn.dataset.view));
      });
      document.getElementById('refreshBtn').addEventListener('click', () => {
        refreshAll().catch((err) => alert(String(err)));
      });
      document.getElementById('saveTasksBtn').addEventListener('click', () => {
        saveTasks().catch((err) => alert(String(err)));
      });
      document.getElementById('saveMemoryBtn').addEventListener('click', () => {
        saveMemory().catch((err) => alert(String(err)));
      });
      document.getElementById('chatForm').addEventListener('submit', (event) => {
        event.preventDefault();
        const input = document.getElementById('chatInput');
        const prompt = safeText(input.value).trim();
        if (!prompt) return;
        input.value = '';
        sendChat(prompt).catch((err) => addChatBubble('Error: ' + String(err), 'bot'));
      });

      document.getElementById('openSpotlight').addEventListener('click', showSpotlight);
      document.getElementById('spotlightOverlay').addEventListener('click', (event) => {
        if (event.target.id === 'spotlightOverlay') hideSpotlight();
      });
      document.getElementById('spotlightInput').addEventListener('input', (event) => {
        renderSpotlightResults(event.target.value);
      });

      document.addEventListener('keydown', (event) => {
        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
          event.preventDefault();
          showSpotlight();
        } else if (event.key === 'Escape') {
          hideSpotlight();
        }
      });
    }

    async function boot() {
      setupInteractions();
      setupTimer();
      try {
        await refreshAll();
      } catch (err) {
        document.getElementById('metaLine').textContent = 'Failed to load cockpit data';
        addChatBubble('Startup error: ' + String(err), 'bot');
      }
      setInterval(() => {
        refreshAll().catch(() => {});
      }, 7000);
    }

    boot();
  </script>
</body>
</html>
"""


@dataclass(frozen=True)
class CockpitRuntimePaths:
    tasks_path: Path
    memory_dir: Path
    output_dir: Path
    config: ProductivityCockpitConfig | None


def _current_branch(project_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=2.0,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    branch = (result.stdout or "").strip()
    return branch or None


def _resolve_feature_tasks_path(project_root: Path) -> str | None:
    branch = _current_branch(project_root)
    if not branch:
        return None
    if not CANONICAL_FEATURE_BRANCH_RE.fullmatch(branch):
        return None
    candidate = project_root / "specs" / branch / "tasks.md"
    if not candidate.exists():
        return None
    return str(candidate.relative_to(project_root))


def _resolve_runtime_paths(project_root: Path) -> CockpitRuntimePaths:
    config = load_cockpit_config(project_root)
    tasks_raw = config.paths.tasks if config else None
    tasks_fallback_raw = config.paths.tasks_fallback if config else None
    memory_raw = config.paths.memory if config else None
    output_raw = config.paths.output if config else None

    tasks_candidate = resolve_optional_project_relative_path(project_root, tasks_raw, field_name="paths.tasks")
    if tasks_candidate and tasks_candidate.exists():
        tasks_path = tasks_candidate
    else:
        tasks_fallback = resolve_optional_project_relative_path(
            project_root,
            tasks_fallback_raw,
            field_name="paths.tasks_fallback",
        )
        if tasks_fallback and tasks_fallback.exists():
            tasks_path = tasks_fallback
        else:
            feature_tasks = _resolve_feature_tasks_path(project_root)
            if feature_tasks:
                tasks_path = resolve_project_relative_path(
                    project_root,
                    feature_tasks,
                    field_name="feature tasks path",
                )
            else:
                tasks_path = resolve_project_relative_path(
                    project_root,
                    "TASKS.md",
                    field_name="default tasks path",
                )

    memory_dir = resolve_optional_project_relative_path(project_root, memory_raw, field_name="paths.memory")
    if memory_dir is None:
        memory_dir = resolve_project_relative_path(project_root, "memory", field_name="default memory path")

    output_dir = resolve_optional_project_relative_path(project_root, output_raw, field_name="paths.output")
    if output_dir is None:
        output_dir = resolve_project_relative_path(project_root, "output", field_name="default output path")

    return CockpitRuntimePaths(
        tasks_path=ensure_path_within_project_root(project_root, tasks_path, field_name="tasks path"),
        memory_dir=ensure_path_within_project_root(project_root, memory_dir, field_name="memory path"),
        output_dir=ensure_path_within_project_root(project_root, output_dir, field_name="output path"),
        config=config,
    )


def _safe_rel(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_tasks_markdown(text: str) -> dict[str, list[dict[str, Any]]]:
    sections: dict[str, list[dict[str, Any]]] = {name: [] for name in TASK_SECTION_ORDER}
    current: str | None = None
    for line in text.splitlines():
        heading = re.match(r"^\s*##\s+(?P<label>.+?)\s*$", line)
        if heading:
            label = heading.group("label").strip()
            current = label if label in sections else None
            continue
        if not current:
            continue
        match = TASK_LINE_RE.match(line)
        if not match:
            continue
        body = match.group("body").strip()
        checked = match.group("checked").lower() == "x"
        sections[current].append({"body": body, "checked": checked})
    return sections


def _render_tasks_markdown(sections: dict[str, list[dict[str, Any]]]) -> str:
    lines = ["# Tasks", ""]
    for section in TASK_SECTION_ORDER:
        lines.append(f"## {section}")
        for item in sections.get(section, []):
            body = " ".join(str(item.get("body", "")).split()).strip()
            if not body:
                continue
            checked = bool(item.get("checked"))
            marker = "x" if checked else " "
            lines.append(f"- [{marker}] {body}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _load_tasks_payload(tasks_path: Path) -> dict[str, Any]:
    if not tasks_path.exists():
        sections = {name: [] for name in TASK_SECTION_ORDER}
    else:
        sections = _parse_tasks_markdown(tasks_path.read_text(encoding="utf-8"))

    summary = {
        "total": 0,
        "checked": 0,
        "by_section": {},
    }
    for section in TASK_SECTION_ORDER:
        rows = sections.get(section, [])
        total = len(rows)
        checked = len([row for row in rows if row.get("checked")])
        summary["by_section"][section] = total
        summary["total"] += total
        summary["checked"] += checked

    return {
        "sections": sections,
        "summary": summary,
    }


def _coerce_sections_payload(payload: Any) -> dict[str, list[dict[str, Any]]]:
    raw = payload.get("sections") if isinstance(payload, dict) else None
    if not isinstance(raw, dict):
        raise ValueError("Expected object with 'sections'.")

    normalized: dict[str, list[dict[str, Any]]] = {name: [] for name in TASK_SECTION_ORDER}
    for section in TASK_SECTION_ORDER:
        rows = raw.get(section, [])
        if not isinstance(rows, list):
            raise ValueError(f"Section '{section}' must be a list.")
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError(f"Invalid task item in section '{section}'.")
            body = " ".join(str(row.get("body", "")).split()).strip()
            if not body:
                continue
            normalized[section].append({"body": body, "checked": bool(row.get("checked", False))})
    return normalized


def _collect_memory_files(memory_dir: Path, project_root: Path) -> list[dict[str, str]]:
    if not memory_dir.exists():
        return []
    files: list[dict[str, str]] = []
    for path in sorted(memory_dir.rglob("*")):
        if len(files) >= MAX_MEMORY_FILES:
            break
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".txt"}:
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size > MAX_MEMORY_FILE_BYTES:
            continue
        try:
            preview = path.read_text(encoding="utf-8")[:180].replace("\n", " ").strip()
        except (UnicodeDecodeError, OSError):
            continue
        files.append({"path": _safe_rel(path, project_root), "preview": preview})
    return files


def _resolve_memory_target(project_root: Path, raw_path: str) -> Path:
    normalized = PurePosixPath(str(raw_path).replace("\\", "/"))
    if normalized.is_absolute() or ".." in normalized.parts:
        raise ValueError("memory.path must be project-relative without path traversal.")
    if not normalized.parts:
        raise ValueError("memory.path must not be empty.")
    target = (project_root / normalized.as_posix()).resolve()
    return ensure_path_within_project_root(project_root, target, field_name="memory.path")


def _truncate_output(value: str, max_chars: int = MAX_EXEC_OUTPUT_CHARS) -> str:
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 3] + "..."


def _sanitize_cli_args(args: list[str]) -> list[str]:
    if len(args) > MAX_CLI_ARGS:
        raise ValueError(f"Too many CLI args. Maximum allowed is {MAX_CLI_ARGS}.")
    normalized: list[str] = []
    for raw in args:
        token = str(raw).strip()
        if not token:
            continue
        if len(token) > MAX_CLI_ARG_CHARS:
            raise ValueError("CLI arg exceeds maximum length.")
        if not ALLOWED_CLI_ARG_RE.fullmatch(token):
            raise ValueError(
                "Unsupported CLI arg format. Allowed format is '--flag' or '--flag=value'."
            )
        normalized.append(token)
    return normalized


def _exec_cli_mode(
    *,
    project_root: Path,
    cli: str,
    args: list[str],
    prompt: str,
    timeout: float = 45.0,
) -> dict[str, Any]:
    command = cli.strip()
    if command not in ALLOWED_AI_CLIS:
        joined = ", ".join(sorted(ALLOWED_AI_CLIS))
        raise ValueError(f"CLI '{command}' is not allowed. Allowed: {joined}.")

    safe_args = _sanitize_cli_args(args)
    # "--" forces prompt to be treated as a positional value, not a flag.
    cmd = [command, *safe_args, "--", prompt]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            cwd=str(project_root),
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"CLI '{command}' not found on PATH.") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"CLI execution timed out after {timeout:.0f}s.") from exc

    return {
        "stdout": _truncate_output(result.stdout),
        "stderr": _truncate_output(result.stderr),
        "exit_code": result.returncode,
        "mode": "cli",
        "cli": command,
    }


def _exec_api_mode(*, provider: str, model: str, prompt: str, timeout: float = 45.0) -> dict[str, Any]:
    provider_norm = provider.strip().lower()
    if provider_norm in {"", "none"}:
        raise ValueError("API mode requires 'provider'.")

    if provider_norm == "ollama":
        ollama_base_url = (os.getenv("OLLAMA_HOST") or "http://127.0.0.1:11434").strip().rstrip("/")
        if not ollama_base_url.startswith(("http://", "https://")):
            raise ValueError("OLLAMA_HOST must start with http:// or https://.")
        body = json.dumps({"model": model or "llama3.1:8b", "prompt": prompt, "stream": False}).encode("utf-8")
        request = Request(
            f"{ollama_base_url}/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (URLError, HTTPError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc
        return {
            "stdout": _truncate_output(str(payload.get("response", ""))),
            "stderr": "",
            "exit_code": 0,
            "mode": "api",
            "provider": provider_norm,
            "model": model or "llama3.1:8b",
        }

    if provider_norm == "openai":
        api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured for API mode.")
        body = json.dumps(
            {
                "model": model or "gpt-4o",
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode("utf-8")
        request = Request(
            "https://api.openai.com/v1/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (URLError, HTTPError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"OpenAI API request failed: {exc}") from exc
        choices = payload.get("choices", [])
        first_choice = choices[0] if isinstance(choices, list) and choices else {}
        text = first_choice.get("message", {}).get("content", "") if isinstance(first_choice, dict) else ""
        return {
            "stdout": _truncate_output(str(text)),
            "stderr": "",
            "exit_code": 0,
            "mode": "api",
            "provider": provider_norm,
            "model": model or "gpt-4o",
        }

    raise ValueError("Unsupported provider for API mode. Supported: ollama, openai.")


def _status_payload(*, project_root: Path, host: str, port: int, started_at: float) -> dict[str, Any]:
    runtime = _resolve_runtime_paths(project_root)
    return {
        "service": SERVICE_NAME,
        "host": host,
        "port": port,
        "project_root": str(project_root),
        "started_at_epoch": started_at,
        "uptime_seconds": round(time.time() - started_at, 3),
        "paths": {
            "tasks": _safe_rel(runtime.tasks_path, project_root),
            "memory": _safe_rel(runtime.memory_dir, project_root),
            "output": _safe_rel(runtime.output_dir, project_root),
        },
        "artifacts": {
            "tasks": runtime.tasks_path.exists(),
            "claude": (project_root / "CLAUDE.md").exists(),
            "memory": runtime.memory_dir.exists(),
            "cockpit_config": (project_root / ".cockpit.json").exists(),
        },
        "drift": {
            "watching": [
                _safe_rel(runtime.tasks_path, project_root),
                _safe_rel(runtime.memory_dir, project_root),
            ],
        },
    }


def _pulse_payload(project_root: Path, runtime: CockpitRuntimePaths) -> dict[str, Any]:
    config = runtime.config
    pulse_rules = config.pulse_rules if config else None
    essential_files = tuple(pulse_rules.essential_files) if pulse_rules else ("README.md",)
    min_folders = tuple(pulse_rules.min_folders) if pulse_rules else ()

    essential_checks: list[dict[str, Any]] = []
    for rel in essential_files:
        try:
            path = resolve_project_relative_path(project_root, rel, field_name=f"pulse essential file '{rel}'")
        except ValueError:
            essential_checks.append({"label": rel, "exists": False, "detail": "invalid path in config"})
            continue
        exists = path.exists()
        essential_checks.append({"label": rel, "exists": exists, "detail": _safe_rel(path, project_root)})

    folder_checks: list[dict[str, Any]] = []
    for rel in min_folders:
        try:
            path = resolve_project_relative_path(project_root, rel, field_name=f"pulse folder '{rel}'")
        except ValueError:
            folder_checks.append(
                {"label": rel, "exists": False, "warning": True, "detail": "invalid folder path in config"}
            )
            continue
        exists = path.exists() and path.is_dir()
        folder_checks.append({"label": rel, "exists": exists, "warning": True, "detail": _safe_rel(path, project_root)})

    task_counts = _load_tasks_payload(runtime.tasks_path)["summary"]
    return {
        "essential_files": essential_checks,
        "min_folders": folder_checks,
        "task_counts": task_counts,
        "generated_at": _iso_now(),
    }


def _scan_drift_snapshot(project_root: Path, runtime: CockpitRuntimePaths) -> dict[str, float]:
    watched = [runtime.tasks_path]
    if runtime.memory_dir.exists() and runtime.memory_dir.is_dir():
        watched.extend(path for path in runtime.memory_dir.rglob("*") if path.is_file())
    snapshot: dict[str, float] = {}
    for path in watched:
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        rel = _safe_rel(path, project_root)
        snapshot[rel] = mtime
    return snapshot


def build_handler(project_root: Path, host: str, port: int, started_at: float) -> type[BaseHTTPRequestHandler]:
    drift_lock = threading.Lock()
    drift_state: dict[str, Any] = {"cursor": 0, "snapshot": {}}

    class Handler(BaseHTTPRequestHandler):
        def _send_common_security_headers(self) -> None:
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Cross-Origin-Resource-Policy", "same-origin")

        def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self._send_common_security_headers()
            self.end_headers()
            self.wfile.write(body)

        def _send_html(self, html: str, status: int = 200) -> None:
            body = html.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self._send_common_security_headers()
            self.send_header(
                "Content-Security-Policy",
                (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline'; "
                    "style-src 'self' 'unsafe-inline'; "
                    "img-src 'self' data:; "
                    "object-src 'none'; "
                    "base-uri 'none'; "
                    "frame-ancestors 'none'; "
                    "connect-src 'self'"
                ),
            )
            self.end_headers()
            self.wfile.write(body)

        def _read_json_body(self) -> dict[str, Any]:
            content_type = self.headers.get("Content-Type", "")
            media_type = content_type.split(";", 1)[0].strip().lower()
            if media_type != "application/json":
                raise ValueError("Content-Type must be application/json.")

            allowed_origins = {f"http://{host}:{port}", f"http://localhost:{port}"}
            sec_fetch_site = (self.headers.get("Sec-Fetch-Site") or "").strip().lower()
            if sec_fetch_site and sec_fetch_site not in {"same-origin", "same-site", "none"}:
                raise ValueError("Cross-site requests are not allowed.")

            origin = (self.headers.get("Origin") or "").strip()
            if origin and origin not in allowed_origins:
                raise ValueError("Origin is not allowed.")

            referer = (self.headers.get("Referer") or "").strip()
            if not origin and referer:
                parsed_referer = urlparse(referer)
                referer_origin = (
                    f"{parsed_referer.scheme}://{parsed_referer.netloc}"
                    if parsed_referer.scheme and parsed_referer.netloc
                    else ""
                )
                if referer_origin not in allowed_origins:
                    raise ValueError("Referer origin is not allowed.")

            raw_len = self.headers.get("Content-Length", "").strip()
            if not raw_len.isdigit():
                raise ValueError("Missing or invalid Content-Length.")
            content_length = int(raw_len)
            if content_length < 0 or content_length > MAX_REQUEST_BODY_BYTES:
                raise ValueError("Request body exceeds size limit.")
            data = self.rfile.read(content_length)
            try:
                payload = json.loads(data.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError("Request body must be valid UTF-8 JSON.") from exc
            if not isinstance(payload, dict):
                raise ValueError("Request JSON must be an object.")
            return payload

        def _runtime_paths(self) -> CockpitRuntimePaths:
            return _resolve_runtime_paths(project_root)

        def _drift_payload(self, runtime: CockpitRuntimePaths) -> dict[str, Any]:
            new_snapshot = _scan_drift_snapshot(project_root, runtime)
            with drift_lock:
                previous: dict[str, float] = dict(drift_state["snapshot"])
                changed: list[str] = []
                for path, mtime in new_snapshot.items():
                    if path not in previous or previous[path] != mtime:
                        changed.append(path)
                for path in previous:
                    if path not in new_snapshot:
                        changed.append(path)
                drift_state["cursor"] += 1
                drift_state["snapshot"] = new_snapshot
                cursor = drift_state["cursor"]
            return {
                "cursor": cursor,
                "changed": sorted(changed),
                "tracked_files": len(new_snapshot),
                "generated_at": _iso_now(),
            }

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            runtime = self._runtime_paths()

            if parsed.path == "/api/status":
                self._send_json(_status_payload(project_root=project_root, host=host, port=port, started_at=started_at))
                return

            if parsed.path == "/api/config":
                config = runtime.config.to_dict() if runtime.config else {}
                self._send_json({"config": config})
                return

            if parsed.path == "/api/tasks":
                payload = _load_tasks_payload(runtime.tasks_path)
                payload["path"] = _safe_rel(runtime.tasks_path, project_root)
                self._send_json(payload)
                return

            if parsed.path == "/api/memory":
                query = parse_qs(parsed.query)
                requested = (query.get("path") or [""])[0].strip()
                if requested:
                    try:
                        target = _resolve_memory_target(project_root, requested)
                    except ValueError as exc:
                        self._send_json({"error": str(exc), "code": "invalid_path"}, status=400)
                        return
                    if not target.exists() or not target.is_file():
                        self._send_json({"error": f"Memory file not found: {requested}", "code": "not_found"}, status=404)
                        return
                    if target.stat().st_size > MAX_MEMORY_FILE_BYTES:
                        self._send_json(
                            {"error": "Memory file exceeds size limit.", "code": "file_too_large"},
                            status=413,
                        )
                        return
                    try:
                        content = target.read_text(encoding="utf-8")
                    except (OSError, UnicodeDecodeError) as exc:
                        self._send_json({"error": f"Could not read memory file: {exc}", "code": "read_failed"}, status=400)
                        return
                    self._send_json({"path": _safe_rel(target, project_root), "content": content})
                    return

                files = _collect_memory_files(runtime.memory_dir, project_root)
                self._send_json({"files": files, "root": _safe_rel(runtime.memory_dir, project_root)})
                return

            if parsed.path == "/api/pulse":
                self._send_json(_pulse_payload(project_root, runtime))
                return

            if parsed.path == "/api/drift":
                self._send_json(self._drift_payload(runtime))
                return

            if parsed.path in {"/", "/index.html"}:
                self._send_html(HTML_PAGE)
                return

            self._send_json({"error": "not found", "code": "not_found"}, status=404)

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            runtime = self._runtime_paths()

            try:
                payload = self._read_json_body()
            except ValueError as exc:
                self._send_json({"error": str(exc), "code": "invalid_request"}, status=400)
                return

            if parsed.path == "/api/tasks":
                try:
                    sections = _coerce_sections_payload(payload)
                except ValueError as exc:
                    self._send_json({"error": str(exc), "code": "invalid_tasks_payload"}, status=400)
                    return
                body = _render_tasks_markdown(sections)
                try:
                    _ensure_parent(runtime.tasks_path)
                    runtime.tasks_path.write_text(body, encoding="utf-8")
                except OSError as exc:
                    self._send_json({"error": f"Could not write tasks file: {exc}", "code": "write_failed"}, status=500)
                    return
                self._send_json({"ok": True, "path": _safe_rel(runtime.tasks_path, project_root)})
                return

            if parsed.path == "/api/memory":
                raw_path = str(payload.get("path", "")).strip()
                if not raw_path:
                    self._send_json({"error": "memory.path is required.", "code": "invalid_path"}, status=400)
                    return
                content = str(payload.get("content", ""))
                if len(content.encode("utf-8")) > MAX_MEMORY_CONTENT_BYTES:
                    self._send_json(
                        {"error": "Memory content exceeds size limit.", "code": "content_too_large"},
                        status=413,
                    )
                    return
                try:
                    target = _resolve_memory_target(project_root, raw_path)
                except ValueError as exc:
                    self._send_json({"error": str(exc), "code": "invalid_path"}, status=400)
                    return
                try:
                    _ensure_parent(target)
                    target.write_text(content, encoding="utf-8")
                except OSError as exc:
                    self._send_json({"error": f"Could not write memory file: {exc}", "code": "write_failed"}, status=500)
                    return
                self._send_json({"ok": True, "path": _safe_rel(target, project_root)})
                return

            if parsed.path == "/api/exec":
                prompt = str(payload.get("prompt", "")).strip()
                if not prompt:
                    self._send_json({"error": "prompt is required.", "code": "invalid_prompt"}, status=400)
                    return
                if len(prompt) > MAX_PROMPT_CHARS:
                    self._send_json(
                        {"error": f"Prompt exceeds {MAX_PROMPT_CHARS} characters.", "code": "prompt_too_large"},
                        status=413,
                    )
                    return

                ai_defaults = runtime.config.ai if runtime.config else None
                mode = str(payload.get("mode", ai_defaults.mode if ai_defaults else "cli")).strip().lower()
                if mode not in {"cli", "api"}:
                    self._send_json({"error": "mode must be 'cli' or 'api'.", "code": "invalid_mode"}, status=400)
                    return

                try:
                    if mode == "cli":
                        cli = str(ai_defaults.cli if ai_defaults else "").strip() or "codex"
                        raw_args = list(ai_defaults.args) if ai_defaults else []
                        result = _exec_cli_mode(
                            project_root=project_root,
                            cli=cli,
                            args=[item for item in raw_args if str(item).strip()],
                            prompt=prompt,
                        )
                    else:
                        provider = str(payload.get("provider", ai_defaults.provider if ai_defaults else "")).strip()
                        model = str(payload.get("model", ai_defaults.model if ai_defaults else "")).strip()
                        result = _exec_api_mode(provider=provider, model=model, prompt=prompt)
                except ValueError as exc:
                    self._send_json({"error": str(exc), "code": "invalid_exec_request"}, status=400)
                    return
                except RuntimeError as exc:
                    self._send_json({"error": str(exc), "code": "exec_failed"}, status=502)
                    return

                self._send_json(result)
                return

            self._send_json({"error": "not found", "code": "not_found"}, status=404)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            LOGGER.info(format, *args)

    return Handler


def _validate_project_root(project_root: Path) -> Path:
    root = project_root.resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Invalid project root: {root}")

    cwd = Path.cwd().resolve()
    if root != cwd:
        try:
            root.relative_to(cwd)
        except ValueError as exc:
            raise ValueError(
                f"Invalid project root: {root}. Root must be current working directory or a child path."
            ) from exc
    return root


def run_server(project_root: Path, host: str, port: int) -> int:
    try:
        root = _validate_project_root(project_root)
    except ValueError as exc:
        print(str(exc), flush=True)
        return 2

    started_at = time.time()
    handler = build_handler(root, host, port, started_at)
    server = ThreadingHTTPServer((host, port), handler)
    server.daemon_threads = True
    LOGGER.info("%s listening on http://%s:%s", SERVICE_NAME, host, port)
    LOGGER.info("project_root=%s", root)

    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    except Exception:
        LOGGER.exception("Bridge server stopped due to unexpected error")
        return 1
    finally:
        server.server_close()
    return 0


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run native productivity cockpit bridge.")
    parser.add_argument("--project-root", required=True, help="Project root path.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind.")
    parser.add_argument("--port", default=8001, type=int, help="Port to bind.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="[bridge] %(message)s")
    args = _parse_args(argv)
    return run_server(Path(args.project_root), args.host, int(args.port))


if __name__ == "__main__":
    sys.exit(main())
