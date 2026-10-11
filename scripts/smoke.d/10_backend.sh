# [BE] Phase 0 smoke: token auth + mock-able user creation.
test "$(curl -s -o /dev/null -w '%{http_code}' "$B/health")" = 401
UID_=$(curl -sf -H "$H" -XPOST "$B/users" | sed 's/.*"user_id":"\([^"]*\)".*/\1/')
test -n "$UID_"
# TODO [BE] Phase 1: capture fixture, /analyze v0, attack set
