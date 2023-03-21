#!/bin/bash
set -e

BASE_URL="${BASE_URL:-http://127.0.0.1:9987}"
BASIC_AUTH="${BASIC_AUTH:-}"
ACCOUNT_ID="${ACCOUNT_ID:-}"

EXTRA_CURL_ARGS=()
if [ "$BASIC_AUTH" ]; then
  EXTRA_CURL_ARGS+=("--user" "$BASIC_AUTH")
fi


declare -A roleMap
roleMap["user"]="👨"
roleMap["assistant"]="💻"

cmd_accounts() {
  local json_str exit_code=0
  json_str="$(curl "${EXTRA_CURL_ARGS[@]}" --fail-with-body -s "$BASE_URL/api/account/list")" || exit_code="$?"
  if [ "$exit_code" != "0" ]; then
    echo "$json_str"
    return "$exit_code"
  fi
  local id email valid disabled counter disabled_color valid_color
  while read -r id email valid disabled counter; do
    if [ "$disabled" == "true" ]; then
      disabled_color=90
    else
      disabled_color=37
    fi
    if [ "$valid" == "true" ]; then
      valid_color=92
    else
      valid_color=31
    fi
    printf '\e[1;%sm%s\e[0m \e[1;%sm%s\e[0m \e[1;%sm%s\e[0m\n' \
      "$disabled_color" "$id" \
      "$valid_color" "$email" \
      "$disabled_color" "$counter" \
      "$@"
  done < <(jq -r '.[] | "\(.id) \(.email) \(.is_logged_in) \(.is_disabled) \(.counter)"' <<< "$json_str")
}

cmd_login() {
  local json_str exit_code=0
  json_str="$(curl "${EXTRA_CURL_ARGS[@]}" --fail-with-body -s -X PATCH "$BASE_URL/api/account/login?account=${ACCOUNT_ID}")" || exit_code="$?"
  if [ "$exit_code" != "0" ]; then
    echo "$json_str"
    return "$exit_code"
  fi
  jq -r . <<< "$json_str"
}

cmd_login2() {
  local session_token
  session_token="$(cat)"
  local json_str exit_code=0
  json_str="$(curl "${EXTRA_CURL_ARGS[@]}" --fail-with-body -s -d "$session_token" "$BASE_URL/api/account/login?account=${ACCOUNT_ID}")" || exit_code="$?"
  if [ "$exit_code" != "0" ]; then
    echo "$json_str"
    return "$exit_code"
  fi
  jq -r . <<< "$json_str"
}

cmd_apply() {
  local session_token
  session_token="$(cat)"
  local json_str exit_code=0
  json_str="$(curl "${EXTRA_CURL_ARGS[@]}" --fail-with-body -s -X PUT -d "$session_token" "$BASE_URL/api/account")" || exit_code="$?"
  if [ "$exit_code" != "0" ]; then
    echo "$json_str"
    return "$exit_code"
  fi
  jq -r . <<< "$json_str"
}

cmd_apply2() {
  local email="$1"
  local password="$2"
  local json_str exit_code=0
  json_str="$(curl "${EXTRA_CURL_ARGS[@]}" --fail-with-body -s -X PUT "$BASE_URL/api/account?account=${ACCOUNT_ID}&email=${email}&password=${password}")" || exit_code="$?"
  if [ "$exit_code" != "0" ]; then
    echo "$json_str"
    return "$exit_code"
  fi
  jq -r . <<< "$json_str"
}

cmd_info() {
  local json_str exit_code=0
  json_str="$(curl "${EXTRA_CURL_ARGS[@]}" --fail-with-body -s "$BASE_URL/api/account?account=${ACCOUNT_ID}")" || exit_code="$?"
  if [ "$exit_code" != "0" ]; then
    echo "$json_str"
    return "$exit_code"
  fi
  jq -r . <<< "$json_str"
}

cmd_disable() {
  local json_str exit_code=0
  json_str="$(curl "${EXTRA_CURL_ARGS[@]}" --fail-with-body -s -X PATCH "$BASE_URL/api/account/disable?account=${ACCOUNT_ID}")" || exit_code="$?"
  if [ "$exit_code" != "0" ]; then
    echo "$json_str"
    return "$exit_code"
  fi
  jq -r . <<< "$json_str"
}

cmd_enable() {
  local json_str exit_code=0
  json_str="$(curl "${EXTRA_CURL_ARGS[@]}" --fail-with-body -s -X PATCH "$BASE_URL/api/account/enable?account=${ACCOUNT_ID}")" || exit_code="$?"
  if [ "$exit_code" != "0" ]; then
    echo "$json_str"
    return "$exit_code"
  fi
  jq -r . <<< "$json_str"
}

cmd_models() {
  local json_str exit_code=0
  json_str="$(curl "${EXTRA_CURL_ARGS[@]}" --fail-with-body -s "$BASE_URL/api/models?account=${ACCOUNT_ID}")" || exit_code="$?"
  if [ "$exit_code" != "0" ]; then
    echo "$json_str"
    return "$exit_code"
  fi
  jq -r '.' <<< "$json_str"
}

cmd_list() {
  local limit="$1"
  local offset="$2"
  local json_str exit_code=0
  json_str="$(curl "${EXTRA_CURL_ARGS[@]}" --fail-with-body -s "$BASE_URL/api/conversations?account=${ACCOUNT_ID}&limit=${limit}&offset=${offset}")" || exit_code="$?"
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
    json_str="$(curl "${EXTRA_CURL_ARGS[@]}" --fail-with-body -s -X POST "$BASE_URL/api/title?account=${ACCOUNT_ID}&id=${id}&mid=${mid}")" || exit_code="$?"
    if [ "$exit_code" != "0" ]; then
      echo "$json_str"
      return "$exit_code"
    fi
    jq -r '.' <<< "$json_str"
    return
  fi
  title="$2"
  local json_str exit_code=0
  json_str="$(curl "${EXTRA_CURL_ARGS[@]}" --fail-with-body --data-binary "$title" -s -X PATCH "$BASE_URL/api/title?account=${ACCOUNT_ID}&id=${id}")" || exit_code="$?"
  if [ "$exit_code" != "0" ]; then
    echo "$json_str"
    return "$exit_code"
  fi
  jq -r '.' <<< "$json_str"
}

cmd_history() {
  local id="$1"
  local json_str exit_code=0
  json_str="$(curl "${EXTRA_CURL_ARGS[@]}" --fail-with-body -s "$BASE_URL/api/history?account=${ACCOUNT_ID}&id=${id}")" || exit_code="$?"
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
    role="$(jq -r ".mapping.\"${current_node}\".message.author.role" <<< "$json_str")"
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

cmd_delete() {
  local id="$1"
  local json_str exit_code=0
  json_str="$(curl "${EXTRA_CURL_ARGS[@]}" --fail-with-body -s -X DELETE "$BASE_URL/api/conversation?account=${ACCOUNT_ID}&id=${id}")" || exit_code="$?"
  if [ "$exit_code" != "0" ]; then
    echo "$json_str"
    return "$exit_code"
  fi
  jq -r '.' <<< "$json_str"
}

cmd_dump() {
  local id="$1"
  local json_str exit_code=0
  json_str="$(curl "${EXTRA_CURL_ARGS[@]}" --fail-with-body -s "$BASE_URL/api/history?account=${ACCOUNT_ID}&id=${id}")" || exit_code="$?"
  if [ "$exit_code" != "0" ]; then
    echo "$json_str"
    return "$exit_code"
  fi
  jq -r '.' <<< "$json_str"
}

cmd_send() {
  local msg="$1"
  local id="$2"
  local mid="$3"
  local json_str exit_code=0
  json_str="$(curl "${EXTRA_CURL_ARGS[@]}" --fail-with-body -s --data-binary "$msg" "$BASE_URL/api/send?account=${ACCOUNT_ID}&id=${id}&mid=${mid}")" || exit_code="$?"
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
  local result_mid exit_code=0
  result_mid="$("$0" send "$msg" "$id" "$mid")" || exit_code="$?"
  if [ "$exit_code" != "0" ]; then
    echo "$result_mid"
    return "$exit_code"
  fi
  watch -et -n 0.1 "$0" geti "$result_mid" <<< '' || true
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
  local id mid role msg finished
  id="$(jq -r '.conversation_id' <<< "$json_str")"
  mid="$(jq -r '.message.id' <<< "$json_str")"
  role="$(jq -r '.message.author.role' <<< "$json_str")"
  msg="$(jq -r '.message.content.parts[0]' <<< "$json_str")"
  finished="$(jq -r '.finished' <<< "$json_str")"
  local finished_flag="_"
  if [ "$finished" == "true" ]; then
    finished_flag=""
  fi
  printf '%s\n\n' "$id"
  printf '【%s】 %s\n%s%s\n\n' "${roleMap[$role]}" "${mid}" "${msg}" "${finished_flag}"
}

cmd_getl() {
  local cols
  cols="$(tput cols)"
  local lines
  lines="$(tput lines)"
  local data
  data="$(tail "-$lines")"
  local lines_line=()
  local line
  local n l
  while read -r line; do
    n="$(wc -L <<< "$line")"
    l=$((n/cols))
    if [ $((n%cols)) != 0 ]; then
      l=$((l+1))
    fi
    if [ "$l" == 0 ]; then
      l=1
    fi
    lines_line+=("$l")
  done <<< "$data"
  local i n=0 l=0
  for ((i = $((${#lines_line[@]}-1)); i >= 0; i--)); do
    n="$((n+lines_line[i]))"
    if [ "$n" -gt "$lines" ]; then
      break
    fi
    l=$((l+1))
  done
  echo "$l"
}

cmd_geti() {
  local mid="$1"
  local result
  result="$("$0" get "$mid")"
  local lines
  lines="$(cmd_getl <<< "$result")"
  cat <<< "$result" | tail "-$lines"
  tail -1 <<< "$result" | grep -q '_$'
}

cmd_help(){
  printf 'Usage: %s COMMAND

Commands:
  accounts
  info
  login
  login2
  apply <<< session_token
  apply2 <email> <password>
  disable
  enable

  models
  list [limit] [offset]
  title <id> <mid>
  title <id> <title>
  history <id>
  delete <id>
  dump <id>
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
