#!/bin/bash
set -e

BASE_URL="${BASE_URL:-http://127.0.0.1:9987}"
BASIC_AUTH="${BASIC_AUTH:-}"

EXTRA_CURL_ARGS=()
if [ "$BASIC_AUTH" ]; then
  EXTRA_CURL_ARGS+=("--user" "$BASIC_AUTH")
fi


declare -A roleMap
roleMap["user"]="👨"
roleMap["assistant"]="💻"

cmd_list() {
  local json_str exit_code=0
  json_str="$(curl "${EXTRA_CURL_ARGS[@]}" --fail-with-body -s "$BASE_URL/api/conversations")" || exit_code="$?"
  if [ "$exit_code" != "0" ]; then
    echo "$json_str"
    return "$exit_code"
  fi
  jq -r '.items[] | "\(.id) \(.title)"' <<< "$json_str"
}

cmd_title() {
  local id="$1"
  if [ "${#2}" == 36 ]; then
    mid="$2"
    local json_str exit_code=0
    json_str="$(curl "${EXTRA_CURL_ARGS[@]}" --fail-with-body -s -X POST "$BASE_URL/api/title?id=${id}&mid=${mid}")" || exit_code="$?"
    if [ "$exit_code" != "0" ]; then
      echo "$json_str"
      return "$exit_code"
    fi
    jq -r '.' <<< "$json_str"
    return
  fi
  title="$2"
  local json_str exit_code=0
  json_str="$(curl "${EXTRA_CURL_ARGS[@]}" --fail-with-body --data-binary "$title" -s -X PATCH "$BASE_URL/api/title?id=${id}")" || exit_code="$?"
  if [ "$exit_code" != "0" ]; then
    echo "$json_str"
    return "$exit_code"
  fi
  jq -r '.' <<< "$json_str"
}

cmd_history() {
  local id="$1"
  local json_str exit_code=0
  json_str="$(curl "${EXTRA_CURL_ARGS[@]}" --fail-with-body -s "$BASE_URL/api/history?id=${id}")" || exit_code="$?"
  if [ "$exit_code" != "0" ]; then
    echo "$json_str"
    return "$exit_code"
  fi
  local title
  title="$(jq -r '.title' <<< "$json_str")"
  local current_node
  current_node="$(jq -r '.current_node' <<< "$json_str")"
  local ids=()
  local role msg
  while true; do
    role="$(jq -r ".mapping.\"${current_node}\".message.role" <<< "$json_str")"
    if [ "$role" == null ]; then
      break
    fi
    ids+=("$current_node")
    ids+=("$role")
    msg="$(jq -r ".mapping.\"${current_node}\".message.content.parts[0]" <<< "$json_str")"
    ids+=("$msg")
    current_node="$(jq -r ".mapping.\"${current_node}\".parent" <<< "$json_str")"
  done
  printf -- '--- %s ---\n' "$title"
  printf '%s\n\n' "$id"
  for ((i = $((${#ids[@]}-3)); i >= 0; i-=3)); do
    printf '【%s】 %s\n%s\n\n' "${roleMap[${ids[i+1]}]}" "${ids[i]}" "${ids[i+2]}"
  done
}

cmd_send() {
  local msg="$1"
  local id="$2"
  local mid="$3"
  local json_str exit_code=0
  json_str="$(curl "${EXTRA_CURL_ARGS[@]}" --fail-with-body -s --data-binary "$msg" "$BASE_URL/api/send?id=${id}&mid=${mid}")" || exit_code="$?"
  if [ "$exit_code" != "0" ]; then
    echo "$json_str"
    return "$exit_code"
  fi
  jq -r '.mid' <<< "$json_str"
}

cmd_sendi() {
  local id="$1"
  local mid="$2"
  local msg
  msg="$(cat)"
  echo "正在发送..." >&2
  local result_mid
  result_mid="$("$0" send "$msg" "$id" "$mid")"
  watch -et -n 0.5 "$0" geti "$result_mid" <<< '' || true
  cmd_get "$result_mid"
}

cmd_get() {
  local mid="$1"
  local json_str exit_code=0
  json_str="$(curl "${EXTRA_CURL_ARGS[@]}" --fail-with-body -s "$BASE_URL/api/get?mid=${mid}")" || exit_code="$?"
  if [ "$exit_code" != "0" ]; then
    echo "$json_str"
    return "$exit_code"
  fi
  local id mid role msg end_turn
  id="$(jq -r '.conversation_id' <<< "$json_str")"
  mid="$(jq -r '.message.id' <<< "$json_str")"
  role="$(jq -r '.message.role' <<< "$json_str")"
  msg="$(jq -r '.message.content.parts[0]' <<< "$json_str")"
  end_turn="$(jq -r '.message.end_turn' <<< "$json_str")"
  local end_turn_flag="_"
  if [ "$end_turn" == "true" ]; then
    end_turn_flag=""
  fi
  printf '%s\n\n' "$id"
  printf '【%s】 %s\n%s%s\n\n' "${roleMap[$role]}" "${mid}" "${msg}" "${end_turn_flag}"
}

cmd_geti() {
  local mid="$1"
  local result
  result="$("$0" get "$mid")"
  cat <<< "$result"
  tail -1 <<< "$result" | grep -q '_$'
}

cmd_help(){
  printf 'Usage: %s COMMAND

Commands:
  list
  title <id> <mid>
  title <id> <title>
  history <id>
  send <msg> <id> <mid>
  sendi <id> <mid>  (from stdin)
  get <mid>
  busy

  help
' "$0"
}

main(){
  local cmd="$1"
  shift 2>/dev/null || true
  [ "$cmd" == "" ] && cmd=help  # default command
  [ "$cmd" == "-h" ] || [ "$cmd" == "--help" ] && cmd=help
  if ! type "cmd_$cmd" >/dev/null 2>&1; then
    cmd_help
    return 1
  fi
  cmd_$cmd "$@"
}

main "$@"