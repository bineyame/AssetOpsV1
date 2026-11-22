#!/usr/bin/env bash
# T1: run one heavy command inside the heavy-tool slot pool (specs/T1-heavy-tool-slot-pool/spec.md §2, §3.3).
#
#   tools/heavy-slot.sh [--db | --db-lane] [--wait-seconds <n>] [--label <text>] -- <command> [args...]
#   tools/heavy-slot.sh --status
#
# --db: one heavy database job at a time (both database lanes, db-job.lock then db-job-b.lock). --db-lane: the first
# free database lane, a or b (T1b, specs/T1-heavy-tool-slot-pool/spec-T1b.md §2), for a focused Postgres test run.
#
# Same pool, options, messages and exit codes as tools/heavy-slot.ps1 (the pwsh half takes the same flock(2) locks).
# Exit codes: the child's when the command ran; 64 usage; 69 refused; 75 no slot came free (R20: a child's own 64,
# 69 or 75 is told apart only by this wrapper's stderr line).
#
# The wrapper holds the lock and the child does not (D-T1.2): every value is computed before the first lock open,
# and after it only builtins run (flock on an fd aside, and rm at exit with the lock fds closed).
set -u

hs_usage() {
    [[ -n ${1-} ]] && printf 'heavy-slot: %s\n' "$1" >&2
    printf '%s\n' "usage: tools/heavy-slot.sh [--db | --db-lane] [--wait-seconds <n>] [--label <text>] -- <command> [args...]" \
                  "       tools/heavy-slot.sh --status" >&2
    exit 64
}

hs_db=0
hs_lane=0
hs_wait=1200
hs_label=""
hs_status=0
hs_dd=0
hs_opts=()
while (($#)); do
    case $1 in
        --) shift; hs_dd=1; break ;;
        --db) hs_db=1; hs_opts+=(-Db) ;;
        --db-lane) hs_lane=1; hs_opts+=(-DbLane) ;;
        --status) hs_status=1; hs_opts+=(-Status) ;;
        --wait-seconds)
            [[ ${2-} =~ ^[0-9]+$ ]] || hs_usage "--wait-seconds needs a whole number of seconds."
            hs_wait=$2; hs_opts+=(-SlotWaitSeconds "$2"); shift ;;
        --label)
            (($# >= 2)) || hs_usage "--label needs a text."
            hs_label=$2; hs_opts+=(-Label "$2"); shift ;;
        *) hs_usage "unknown option '$1' (a command goes after --)." ;;
    esac
    shift
done
if ((hs_db && hs_lane)); then
    echo "heavy-slot: --db and --db-lane are exclusive; give one." >&2
    exit 64
fi

if [[ -n ${DOTNET_SYSTEM_IO_DISABLEFILELOCKING:-} ]]; then
    echo "heavy-slot: refused: DOTNET_SYSTEM_IO_DISABLEFILELOCKING is set; the slot locks would not hold." >&2
    exit 69
fi
if ((!hs_status)); then
    ((hs_dd)) || hs_usage "missing -- before the command."
    (($#)) || hs_usage "no command after --."
    [[ $1 == setsid ]] && hs_usage "put setsid/nohup before the wrapper."
fi

hs_here=$(cd -- "${BASH_SOURCE[0]%/*}" 2>/dev/null && pwd -P) || hs_here=$PWD

# No flock(1): hand over to the pwsh half (D-T1.10).
if ! command -v flock >/dev/null 2>&1; then
    if command -v pwsh >/dev/null 2>&1; then
        if ((hs_status)); then exec pwsh -NoProfile -File "$hs_here/heavy-slot.ps1" "${hs_opts[@]}"; fi
        exec pwsh -NoProfile -File "$hs_here/heavy-slot.ps1" "${hs_opts[@]}" -- "$@"
    fi
    echo "heavy-slot: refused: neither flock nor pwsh is available; the slot locks cannot be taken." >&2
    exit 69
fi

# D per spec §2: git's common dir with every GIT_* variable removed, canonical, plus /check-all-slots.
hs_git_common() (
    for hs_v in $(compgen -e); do [[ $hs_v == GIT_* ]] && unset "$hs_v"; done
    git -C "$1" rev-parse --path-format=absolute --git-common-dir 2>/dev/null
)
if [[ -n ${ASSETOPS_HEAVY_SLOT_DIR:-} ]]; then
    mkdir -p -- "$ASSETOPS_HEAVY_SLOT_DIR" && D=$(realpath -e -- "$ASSETOPS_HEAVY_SLOT_DIR") || {
        echo "heavy-slot: refused: cannot use ASSETOPS_HEAVY_SLOT_DIR=$ASSETOPS_HEAVY_SLOT_DIR" >&2; exit 69; }
elif hs_common=$(hs_git_common "$hs_here") && [[ -n $hs_common ]] && hs_c=$(realpath -e -- "$hs_common" 2>/dev/null); then
    D="$hs_c/check-all-slots"
else
    D="$(realpath -e -- "${TMPDIR:-/tmp}")/assetops-check-all-slots"
fi
mkdir -p -- "$D" || { echo "heavy-slot: refused: cannot create $D" >&2; exit 69; }

# A probe: never creates the file, a missing file is free; held when an exclusive flock would block.
hs_held() {
    local fd rc
    [[ -e $1 ]] || return 1
    exec {fd}<"$1" || return 1
    flock -n -E 99 -x "$fd"; rc=$?
    exec {fd}<&-
    ((rc == 99))
}

hs_owner_field() {  # <owner file> <field> -> hs_val (a builtin read: it runs after the lock open too)
    local line
    hs_val=""
    if [[ -r $1 ]]; then
        while IFS= read -r line || [[ -n $line ]]; do [[ $line == "$2="* ]] && hs_val=${line#"$2="}; done < "$1"
    fi
    return 0
}

hs_alive() {  # <pid>: running and not a zombie
    local stat rest
    [[ $1 =~ ^[0-9]+$ ]] || return 1
    IFS= read -r stat 2>/dev/null < "/proc/$1/stat" || return 1
    rest=${stat##*) }
    [[ ${rest:0:1} != Z ]]
}

hs_is_ancestor() {  # <holder> <caller>: the 4th field of /proc/<pid>/stat, parsed after the last ')', 64 steps
    local want=$1 p=$2 i stat rest
    hs_alive "$want" || return 1
    for ((i = 0; i <= 64; i++)); do
        [[ $p == "$want" ]] && return 0
        [[ $p =~ ^[0-9]+$ ]] && ((p > 0)) || return 1
        IFS= read -r stat 2>/dev/null < "/proc/$p/stat" || return 1
        rest=${stat##*) }
        read -r _ p _ <<< "$rest"
    done
    return 1
}

hs_marker() {  # <value> <slot|db|dbb|lane>: the marker test of spec §2 (T1b §2 names); sets hs_reason
    local value=$1 name=$2 dir leaf cdir pid
    if [[ -z $value ]]; then hs_reason="ASSETOPS_HEAVY_SLOT is not set"; return 1; fi
    hs_reason="the marker is not a slot of this machine's pool"
    [[ $value == */* ]] || return 1
    dir=${value%/*}; leaf=${value##*/}
    case $name in
        db) [[ $leaf == db-job.lock ]] ;;
        dbb) [[ $leaf == db-job-b.lock ]] ;;
        lane) [[ $leaf =~ ^db-job(-b)?\.lock$ ]] ;;
        *) [[ $leaf =~ ^slot-[12]\.lock$ ]] ;;
    esac || return 1
    cdir=$(realpath -e -- "${dir:-/}" 2>/dev/null) || return 1
    [[ $cdir == "$D" ]] || return 1
    if [[ -d /proc/self ]]; then
        hs_owner_field "$D/${leaf%.lock}.owner" pid; pid=$hs_val
        hs_reason="the slot's holder is not this process or an ancestor"
        hs_is_ancestor "$pid" "$$" || return 1
    fi
    hs_reason="the slot is not held"
    hs_held "$D/$leaf" || return 1
    hs_reason=""
}

# T1b §2: exclusive passes when both --db markers pass; a lane passes when exclusive does (lane a) or the lane marker.
hs_exclusive() { hs_marker "${ASSETOPS_HEAVY_DB:-}" db && hs_marker "${ASSETOPS_HEAVY_DB_B:-}" dbb; }
hs_lane_held() { hs_exclusive || hs_marker "${ASSETOPS_HEAVY_DB_LANE:-}" lane; }

if ((hs_status)); then
    hs_names=(slot-1 slot-2)
    for hs_f in "$D"/slot-*.lock; do
        [[ -e $hs_f ]] || continue
        hs_n=${hs_f##*/}; hs_n=${hs_n%.lock}
        [[ $hs_n == slot-1 || $hs_n == slot-2 ]] || hs_names+=("$hs_n")
    done
    hs_names+=(db-job db-job-b)
    for hs_n in "${hs_names[@]}"; do
        hs_lock="$D/$hs_n.lock"
        if ! hs_held "$hs_lock"; then echo "$hs_n: free"; continue; fi
        hs_o="$D/$hs_n.owner"
        hs_owner_field "$hs_o" pid; hs_p=$hs_val
        if hs_alive "$hs_p"; then
            hs_line="$hs_n: busy pid=$hs_p"
            for hs_k in child label since cwd; do hs_owner_field "$hs_o" "$hs_k"; hs_line+=" $hs_k=$hs_val"; done
            echo "$hs_line"
        else
            echo "$hs_n: busy, holder unknown (owner file stale); find it with: fuser -v $hs_lock"
        fi
    done
    exit 0
fi

# ---- nesting (D-T1.3, D-T1.13): a verified marker means take nothing ----
if [[ -n ${ASSETOPS_HEAVY_SLOT:-} ]]; then
    if hs_marker "$ASSETOPS_HEAVY_SLOT" slot; then
        if ((hs_db)) && ! hs_exclusive; then
            echo "heavy-slot: refused: --db inside a held slot; put --db on the outermost wrapper." >&2
            exit 69
        fi
        if ((hs_lane)) && ! hs_lane_held; then
            echo "heavy-slot: refused: --db-lane inside a held slot; put --db-lane on the outermost wrapper." >&2
            exit 69
        fi
        exec "$@"
    fi
    printf 'heavy-slot: ignoring stale ASSETOPS_HEAVY_SLOT=%s (%s)\n' "$ASSETOPS_HEAVY_SLOT" "$hs_reason" >&2
fi

# ---- every value before the first lock open ----
[[ -n $hs_label ]] || hs_label="${*:1:2}"
hs_label=${hs_label//$'\n'/ }; hs_label=${hs_label//$'\r'/ }; hs_label=${hs_label//=/ }
hs_cwd=$PWD
hs_db_path="$D/db-job.lock"
hs_dbb_path="$D/db-job-b.lock"
hs_lane_path=""
hs_db_word=no; ((hs_db)) && hs_db_word=yes; ((hs_lane)) && hs_db_word=lane
hs_deadline=$(( ${EPOCHREALTIME/./} + hs_wait * 1000000 ))
exec {hs_sleepfd}<> <(:)   # a pipe nobody writes: `read -t` on it is a builtin sleep

hs_pause() {  # sleep min(2 s, time left) with a builtin
    local left=$(( hs_deadline - ${EPOCHREALTIME/./} )) us frac
    ((left > 0)) || return 0
    us=$(( left < 2000000 ? left : 2000000 ))
    printf -v frac '%06d' $((us % 1000000))
    read -r -t "$((us / 1000000)).$frac" -u "$hs_sleepfd" _
}

hs_timeout() {
    echo "heavy-slot: no slot came free in $hs_wait s (--wait-seconds)." >&2
    exit 75
}

# ---- acquire (T1b §2): --db takes lane a then lane b; --db-lane the first free lane; then the lowest free slot ----
hs_dbfd=""
hs_dbbfd=""
hs_lanefd=""
hs_fds=("$hs_sleepfd")   # every fd number the child and rm must not keep
if ((hs_db)); then
    exec {hs_dbfd}>>"$hs_db_path"
    hs_fds+=("$hs_dbfd")
    hs_said=0
    until flock -n -x "$hs_dbfd"; do
        (( ${EPOCHREALTIME/./} >= hs_deadline )) && hs_timeout
        if ((!hs_said)); then echo "heavy-slot: another database job holds db-job.lock; waiting up to $hs_wait s." >&2; hs_said=1; fi
        hs_pause
    done
    exec {hs_dbbfd}>>"$hs_dbb_path"
    hs_fds+=("$hs_dbbfd")
    hs_said=0
    until flock -n -x "$hs_dbbfd"; do
        (( ${EPOCHREALTIME/./} >= hs_deadline )) && hs_timeout
        if ((!hs_said)); then echo "heavy-slot: another database job holds db-job-b.lock; waiting up to $hs_wait s." >&2; hs_said=1; fi
        hs_pause
    done
elif ((hs_lane)); then
    hs_said=0
    while :; do
        for hs_p in "$hs_db_path" "$hs_dbb_path"; do
            exec {hs_fd}>>"$hs_p"
            if flock -n -x "$hs_fd"; then hs_lanefd=$hs_fd; hs_lane_path=$hs_p; break; fi
            exec {hs_fd}>&-
        done
        [[ -n $hs_lanefd ]] && break
        (( ${EPOCHREALTIME/./} >= hs_deadline )) && hs_timeout
        if ((!hs_said)); then echo "heavy-slot: both database lanes are busy (tools/heavy-slot.sh --status); waiting up to $hs_wait s." >&2; hs_said=1; fi
        hs_pause
    done
    hs_fds+=("$hs_lanefd")
fi
hs_slotfd=""
hs_said=0
while :; do
    for hs_i in 1 2; do
        exec {hs_fd}>>"$D/slot-$hs_i.lock"
        if flock -n -x "$hs_fd"; then hs_slotfd=$hs_fd; hs_n=$hs_i; break; fi
        exec {hs_fd}>&-
    done
    [[ -n $hs_slotfd ]] && break
    (( ${EPOCHREALTIME/./} >= hs_deadline )) && hs_timeout
    if ((!hs_said)); then echo "heavy-slot: both heavy slots are busy (tools/heavy-slot.sh --status); waiting up to $hs_wait s." >&2; hs_said=1; fi
    hs_pause
done

hs_slot_path="$D/slot-$hs_n.lock"
hs_fds+=("$hs_slotfd")
hs_owners=("$D/slot-$hs_n.owner")
((hs_db)) && hs_owners+=("$D/db-job.owner" "$D/db-job-b.owner")
((hs_lane)) && hs_owners+=("${hs_lane_path%.lock}.owner")
TZ=UTC printf -v hs_since '%(%Y-%m-%dT%H:%M:%SZ)T' -1
for hs_o in "${hs_owners[@]}"; do
    printf 'pid=%s\nlabel=%s\nsince=%s\ncwd=%s\ndb=%s\n' "$$" "$hs_label" "$hs_since" "$hs_cwd" "$hs_db_word" > "$hs_o"
done

hs_on_exit() {
    local o keep=()
    for o in "${hs_owners[@]}"; do hs_owner_field "$o" pid; [[ $hs_val == "$$" ]] && keep+=("$o"); done
    # rm runs with every lock fd closed in its own copy (a subshell closes them, then execs rm).
    if ((${#keep[@]})); then
        ( for hs_f in "${hs_fds[@]}"; do exec {hs_f}>&-; done; exec rm -f -- "${keep[@]}" )
    fi
}

hs_child=""
hs_tree=()
hs_collect() {  # <pid>: it and its descendants, through /proc/<pid>/task/*/children
    local f c
    local -a kids
    hs_tree+=("$1")
    for f in /proc/"$1"/task/*/children; do
        [[ -r $f ]] || continue
        read -r -a kids < "$f"
        for c in "${kids[@]}"; do hs_collect "$c"; done
    done
}
hs_on_term() {  # TERM, the deliberate stop (D-T1.15a): TERM the child's tree, wait up to 30 s, KILL what is left
    local i p alive rc
    trap '' TERM HUP INT
    if [[ -n $hs_child ]]; then
        hs_tree=()
        hs_collect "$hs_child"
        kill -TERM "${hs_tree[@]}" 2>/dev/null
        for ((i = 0; i < 300; i++)); do
            alive=0
            for p in "${hs_tree[@]}"; do hs_alive "$p" && { alive=1; break; }; done
            ((alive)) || break
            read -r -t 0.1 -u "$hs_sleepfd" _
        done
        kill -KILL "${hs_tree[@]}" 2>/dev/null
        wait "$hs_child" 2>/dev/null; rc=$?
        ((rc == 127)) && rc=143
        exit "$rc"
    fi
    exit 143
}
hs_nsig=0
hs_on_intr() {  # INT or HUP (D-T1.15a): the first is not forwarded (a terminal or group signal already reached
                # the child); a second is forwarded once to the tree. No timer, never KILL.
    hs_nsig=$((hs_nsig + 1))
    if ((hs_nsig == 2)) && [[ -n $hs_child ]]; then
        hs_tree=()
        hs_collect "$hs_child"
        kill -"$1" "${hs_tree[@]}" 2>/dev/null
    fi
}
trap hs_on_exit EXIT
trap hs_on_term TERM
trap 'hs_on_intr HUP' HUP
trap 'hs_on_intr INT' INT

# ---- the child: it closes the lock fds, keeps stdin and stays in this process group (D-T1.15) ----
# Markers per T1b §2: --db exports both exclusive markers, --db-lane its lane's, neither only the slot.
( trap - INT QUIT
  for hs_f in "${hs_fds[@]}"; do exec {hs_f}>&-; done
  export ASSETOPS_HEAVY_SLOT="$hs_slot_path"
  unset ASSETOPS_HEAVY_DB ASSETOPS_HEAVY_DB_B ASSETOPS_HEAVY_DB_LANE
  if ((hs_db)); then export ASSETOPS_HEAVY_DB="$hs_db_path" ASSETOPS_HEAVY_DB_B="$hs_dbb_path"
  elif ((hs_lane)); then export ASSETOPS_HEAVY_DB_LANE="$hs_lane_path"; fi
  exec "$@" ) <&0 &
hs_child=$!
for hs_o in "${hs_owners[@]}"; do printf 'child=%s\n' "$hs_child" >> "$hs_o"; done

# A trapped INT or HUP interrupts `wait`; keep waiting, with no limit, and exit with the child's own status.
while :; do
    wait "$hs_child"; hs_rc=$?
    hs_alive "$hs_child" || break
done
wait "$hs_child" 2>/dev/null; hs_rc2=$?
((hs_rc2 != 127)) && hs_rc=$hs_rc2
exit "$hs_rc"
