#!/usr/bin/env bash
# T1: run one heavy command inside the heavy-tool slot pool (specs/T1-heavy-tool-slot-pool/spec.md §2, §3.3).
#
#   tools/heavy-slot.sh [--db] [--wait-seconds <n>] [--label <text>] -- <command> [args...]
#   tools/heavy-slot.sh --status
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
    printf '%s\n' "usage: tools/heavy-slot.sh [--db] [--wait-seconds <n>] [--label <text>] -- <command> [args...]" \
                  "       tools/heavy-slot.sh --status" >&2
    exit 64
}

hs_db=0
hs_wait=1200
hs_label=""
hs_status=0
hs_dd=0
hs_opts=()
while (($#)); do
    case $1 in
        --) shift; hs_dd=1; break ;;
        --db) hs_db=1; hs_opts+=(-Db) ;;
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

hs_marker() {  # <value> <slot|db>: the marker test of spec §2; sets hs_reason
    local value=$1 name=$2 dir leaf cdir pid
    if [[ -z $value ]]; then hs_reason="ASSETOPS_HEAVY_SLOT is not set"; return 1; fi
    hs_reason="the marker is not a slot of this machine's pool"
    [[ $value == */* ]] || return 1
    dir=${value%/*}; leaf=${value##*/}
    if [[ $name == db ]]; then [[ $leaf == db-job.lock ]] || return 1
    else [[ $leaf =~ ^slot-[12]\.lock$ ]] || return 1; fi
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

if ((hs_status)); then
    hs_names=(slot-1 slot-2)
    for hs_f in "$D"/slot-*.lock; do
        [[ -e $hs_f ]] || continue
        hs_n=${hs_f##*/}; hs_n=${hs_n%.lock}
        [[ $hs_n == slot-1 || $hs_n == slot-2 ]] || hs_names+=("$hs_n")
    done
    hs_names+=(db-job)
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
        if ((hs_db)) && ! hs_marker "${ASSETOPS_HEAVY_DB:-}" db; then
            echo "heavy-slot: refused: --db inside a held slot; put --db on the outermost wrapper." >&2
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
hs_db_word=no; ((hs_db)) && hs_db_word=yes
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

# ---- acquire: the DB lock first, then the lowest free slot ----
hs_dbfd=""
if ((hs_db)); then
    exec {hs_dbfd}>>"$hs_db_path"
    hs_said=0
    until flock -n -x "$hs_dbfd"; do
        (( ${EPOCHREALTIME/./} >= hs_deadline )) && hs_timeout
        if ((!hs_said)); then echo "heavy-slot: another database job holds db-job.lock; waiting up to $hs_wait s." >&2; hs_said=1; fi
        hs_pause
    done
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
hs_owners=("$D/slot-$hs_n.owner")
((hs_db)) && hs_owners+=("$D/db-job.owner")
TZ=UTC printf -v hs_since '%(%Y-%m-%dT%H:%M:%SZ)T' -1
for hs_o in "${hs_owners[@]}"; do
    printf 'pid=%s\nlabel=%s\nsince=%s\ncwd=%s\ndb=%s\n' "$$" "$hs_label" "$hs_since" "$hs_cwd" "$hs_db_word" > "$hs_o"
done

hs_on_exit() {
    local o keep=()
    for o in "${hs_owners[@]}"; do hs_owner_field "$o" pid; [[ $hs_val == "$$" ]] && keep+=("$o"); done
    if ((${#keep[@]})); then
        if [[ -n $hs_dbfd ]]; then rm -f -- "${keep[@]}" {hs_slotfd}>&- {hs_dbfd}>&- {hs_sleepfd}>&-
        else rm -f -- "${keep[@]}" {hs_slotfd}>&- {hs_sleepfd}>&-; fi
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
hs_on_signal() {  # <exit code>: TERM the child's tree, wait up to 5 s, KILL what is left
    local i p alive
    trap '' TERM HUP INT
    if [[ -n $hs_child ]]; then
        hs_tree=()
        hs_collect "$hs_child"
        kill -TERM "${hs_tree[@]}" 2>/dev/null
        for ((i = 0; i < 50; i++)); do
            alive=0
            for p in "${hs_tree[@]}"; do hs_alive "$p" && { alive=1; break; }; done
            ((alive)) || break
            read -r -t 0.1 -u "$hs_sleepfd" _
        done
        kill -KILL "${hs_tree[@]}" 2>/dev/null
    fi
    exit "$1"
}
trap hs_on_exit EXIT
trap 'hs_on_signal 143' TERM
trap 'hs_on_signal 129' HUP
trap 'hs_on_signal 130' INT

# ---- the child: it closes the lock fds, keeps stdin and stays in this process group (D-T1.15) ----
if ((hs_db)); then
    ( exec {hs_slotfd}>&- {hs_dbfd}>&- {hs_sleepfd}>&-
      export ASSETOPS_HEAVY_SLOT="$hs_slot_path" ASSETOPS_HEAVY_DB="$hs_db_path"
      exec "$@" ) <&0 &
else
    ( exec {hs_slotfd}>&- {hs_sleepfd}>&-
      export ASSETOPS_HEAVY_SLOT="$hs_slot_path"; unset ASSETOPS_HEAVY_DB
      exec "$@" ) <&0 &
fi
hs_child=$!
for hs_o in "${hs_owners[@]}"; do printf 'child=%s\n' "$hs_child" >> "$hs_o"; done

wait "$hs_child"; hs_rc=$?
while hs_alive "$hs_child"; do wait "$hs_child"; hs_rc=$?; done
exit "$hs_rc"
