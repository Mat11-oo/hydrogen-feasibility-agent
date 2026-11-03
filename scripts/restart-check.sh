#!/usr/bin/env bash
# 重启恢复检查钩子：start / write / read / stop（契约见通用手册第十节）。
# verify.sh 自己负责：起服务→写标记→杀进程→再起→读回比对。钩子只提供四个动作。
# 阶段 2-1 用「创建报告」这条不调模型的写入路径来验证持久化。
set -u

PROJECT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$PROJECT/backend"
PORT="${RESTART_CHECK_PORT:-8123}"
BASE="http://127.0.0.1:${PORT}"
LOG="${RESTART_CHECK_DIR:-/tmp}/server.log"
PY="$BACKEND/.venv/bin/python"

start() {
  # 端口被占：不杀别人的进程，直接报错退出
  if lsof -i :"$PORT" >/dev/null 2>&1; then
    echo "端口 ${PORT} 被占用" >&2
    exit 1
  fi
  # 起一个服务实例：数据放临时目录、清空模型 Key（不调真实模型）
  RESTART_CHECK_DIR="${RESTART_CHECK_DIR:-/tmp/kesan-rc}" \
  MODEL_API_KEY="" \
  nohup "$PY" -m uvicorn app.main:app --app-dir "$BACKEND" --host 127.0.0.1 --port "$PORT" >"$LOG" 2>&1 &
  PID=$!
  # 等端口能响应（最多约 9 秒）
  for _ in $(seq 1 30); do
    if curl -s "$BASE/api/v1/reports" >/dev/null 2>&1; then
      echo "$PID"
      return 0
    fi
    if ! kill -0 "$PID" 2>/dev/null; then
      echo "服务进程已退出（日志见 ${LOG}）" >&2
      exit 1
    fi
    sleep 0.3
  done
  kill "$PID" 2>/dev/null
  echo "服务启动超时" >&2
  exit 1
}

write() {
  local mark="$1" resp
  resp="$(curl -s -X POST "$BASE/api/v1/reports" \
    -H 'Content-Type: application/json' \
    -d "{\"title\":\"$mark\",\"target_words\":1000}")"
  echo "$resp" | "$PY" -c 'import sys,json; print(json.load(sys.stdin)["id"])'
}

read() {
  local id="$1" resp
  resp="$(curl -s "$BASE/api/v1/reports/$id")"
  echo "$resp" | "$PY" -c 'import sys,json; print(json.load(sys.stdin)["title"])'
}

stop() {
  # 停掉还在跑的实例（用端口找 PID，不误杀）
  local p
  p="$(lsof -ti :"$PORT" 2>/dev/null)"
  [ -n "$p" ] && kill "$p" 2>/dev/null
  echo "stopped"
}

case "${1:-}" in
  start) start ;;
  write) write "${2:-}" ;;
  read) read "${2:-}" ;;
  stop) stop ;;
  *) echo "用法：restart-check.sh start|write <标记>|read <ID>|stop" >&2; exit 2 ;;
esac
